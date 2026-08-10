from .models import Cart


def get_cart(request):
    if not request.session.session_key:
        request.session.create()

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        session_cart = Cart.objects.filter(session_key=request.session.session_key).exclude(pk=cart.pk).first()
        if session_cart:
            _merge_carts(cart, session_cart)
        return cart

    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def _merge_carts(target, source):
    for item in source.items.all():
        existing = target.items.filter(variant=item.variant).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = target
            item.save()
    source.delete()
