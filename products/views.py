from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .filters import ProductFilter
from .forms import ReviewForm
from .models import Category, Product, StockSubscription, Wishlist

PRODUCTS_PER_PAGE = 24
PRODUCTS_PER_ROW = 5
RELATED_PRODUCTS_COUNT = 8
FEATURED_PRODUCTS_COUNT = 8


def product_list(request, slug=None):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants')
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=category)

    search_query = request.GET.get('q', '')
    is_filtered = bool(search_query or request.GET.get('min_price') or request.GET.get('max_price'))

    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist_product_ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'categories': Category.objects.all(),
        'category': category,
        'search_query': search_query,
        'wishlist_product_ids': wishlist_product_ids,
    }

    if not category and not is_filtered:
        # Browsing the full catalog with no filters - group by category, one row
        # each, with a link through to the category's own paginated page.
        #
        # Ranks every active product within its own category by recency in a
        # single query (instead of one query per category), then keeps the
        # top PRODUCTS_PER_ROW + 1 of each - the "+1" is just to detect
        # whether there's more to show without a separate count query.
        ranked = Product.objects.filter(is_active=True).annotate(
            row_number=Window(
                expression=RowNumber(),
                partition_by=[F('category_id')],
                order_by=F('created_at').desc(),
            ),
        )
        top_products = (
            ranked.filter(row_number__lte=PRODUCTS_PER_ROW + 1)
            .select_related('category').prefetch_related('images', 'variants')
            .order_by('category_id', 'row_number')
        )

        by_category = {}
        for product in top_products:
            by_category.setdefault(product.category_id, []).append(product)

        counts = dict(
            Category.objects.filter(products__is_active=True)
            .annotate(product_count=Count('products')).values_list('id', 'product_count'),
        )

        category_cards = list(context['categories'])
        for cat in category_cards:
            cat.product_count = counts.get(cat.id, 0)
        context['categories'] = category_cards

        sections = []
        for cat in category_cards:
            cat_products = by_category.get(cat.id, [])
            if not cat_products:
                continue
            sections.append({
                'category': cat,
                'product_count': counts.get(cat.id, 0),
                'products': cat_products[:PRODUCTS_PER_ROW],
                'has_more': len(cat_products) > PRODUCTS_PER_ROW,
            })
        context['sections'] = sections
        context['featured_products'] = (
            Product.objects.filter(is_active=True, is_featured=True)
            .select_related('category').prefetch_related('images', 'variants')
            .order_by('-created_at')[:FEATURED_PRODUCTS_COUNT]
        )
        return render(request, 'products/list.html', context)

    filtered = ProductFilter(request.GET, queryset=products)

    paginator = Paginator(filtered.qs, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)

    context.update({
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring.urlencode(),
    })
    return render(request, 'products/list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'variants'),
        slug=slug, is_active=True,
    )
    in_wishlist = (
        request.user.is_authenticated
        and Wishlist.objects.filter(user=request.user, product=product).exists()
    )

    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .select_related('category').prefetch_related('images', 'variants')
        .order_by('-created_at')[:RELATED_PRODUCTS_COUNT]
    )

    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist_product_ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'products/detail.html', {
        'product': product,
        'reviews': product.approved_reviews.select_related('user'),
        'rating_summary': product.rating_summary,
        'can_review': product.can_review(request.user),
        'has_reviewed': product.has_reviewed(request.user),
        'in_wishlist': in_wishlist,
        'related_products': related_products,
        'wishlist_product_ids': wishlist_product_ids,
    })


@login_required
def toggle_wishlist(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    if request.method == 'POST':
        deleted, _ = Wishlist.objects.filter(user=request.user, product=product).delete()
        if not deleted:
            Wishlist.objects.create(user=request.user, product=product)

    in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    return JsonResponse({'in_wishlist': in_wishlist})


def subscribe_stock(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def respond(success, message):
        if is_ajax:
            return JsonResponse({'success': success, 'message': message}, status=200 if success else 400)
        messages.add_message(request, messages.SUCCESS if success else messages.ERROR, message)
        return redirect(product.get_absolute_url())

    if request.method != 'POST':
        return redirect(product.get_absolute_url())

    email = request.POST.get('email', '').strip()
    if not email and request.user.is_authenticated:
        email = request.user.email

    try:
        validate_email(email)
    except ValidationError:
        return respond(False, 'يرجى إدخال بريد إلكتروني صالح.')

    # A specific variant is passed from the product detail page (the option
    # the shopper picked); the bell icon on product cards omits it, meaning
    # "notify me for whichever of this product's variants comes back".
    variants = product.variants.filter(stock=0)
    variant_id = request.POST.get('variant')
    if variant_id and variant_id.isdigit():
        variants = variants.filter(pk=variant_id)

    if not variants.exists():
        return respond(False, 'هذا المنتج متوفر بالفعل في المخزون.')

    created_any = False
    for variant in variants:
        _, created = StockSubscription.objects.get_or_create(variant=variant, email=email)
        created_any = created_any or created

    if created_any:
        return respond(True, 'سنرسل لك بريدًا إلكترونيًا فور توفر المنتج مجددًا.')
    return respond(True, 'أنت مسجّل بالفعل في قائمة الانتظار لهذا المنتج.')


@login_required
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if not product.can_review(request.user):
        messages.error(request, 'يمكنك تقييم المنتجات التي اشتريتها فقط، ومرة واحدة لكل منتج.')
        return redirect(product.get_absolute_url())

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'شكرًا لك! تم إرسال تقييمك وهو الآن قيد المراجعة.')
            return redirect(product.get_absolute_url())
    else:
        form = ReviewForm()

    return render(request, 'products/review_form.html', {'form': form, 'product': product})
