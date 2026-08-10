from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, ListView

from products.models import Category, Product

from ..forms import ProductForm, ProductImageFormSet, VariantFormSet
from ..mixins import AjaxDeleteMixin
from ..permissions import StaffRequiredMixin, SuperuserRequiredMixin


class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/products/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        qs = Product.objects.select_related('category').prefetch_related('images').order_by('-created_at')
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        if q:
            qs = qs.filter(name__icontains=q)
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.order_by('name')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_category'] = self.request.GET.get('category', '')
        return ctx


class ProductFormView(StaffRequiredMixin, View):
    template_name = 'dashboard/products/form.html'

    def get_object(self, pk):
        return get_object_or_404(Product, pk=pk) if pk else None

    def render_form(self, request, product, form, image_formset, variant_formset):
        return render(request, self.template_name, {
            'form': form,
            'image_formset': image_formset,
            'variant_formset': variant_formset,
            'product': product,
        })

    def get(self, request, pk=None):
        product = self.get_object(pk)
        form = ProductForm(instance=product)
        image_formset = ProductImageFormSet(instance=product)
        variant_formset = VariantFormSet(instance=product)
        return self.render_form(request, product, form, image_formset, variant_formset)

    def post(self, request, pk=None):
        product = self.get_object(pk)
        instance_for_formsets = product or Product()

        form = ProductForm(request.POST, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=instance_for_formsets)
        variant_formset = VariantFormSet(request.POST, instance=instance_for_formsets)

        if form.is_valid() and image_formset.is_valid() and variant_formset.is_valid():
            product = form.save()
            image_formset.instance = product
            variant_formset.instance = product
            image_formset.save()
            variant_formset.save()
            messages.success(request, f'تم حفظ المنتج "{product.name}".')
            return redirect('dashboard:product_list')

        return self.render_form(request, product, form, image_formset, variant_formset)


class ProductDeleteView(AjaxDeleteMixin, SuperuserRequiredMixin, DeleteView):
    model = Product
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'حذف "{self.object.name}"؟'
        ctx['cancel_url'] = reverse_lazy('dashboard:product_list')
        return ctx
