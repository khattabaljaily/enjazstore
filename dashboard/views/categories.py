from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from products.models import Category

from ..forms import CategoryForm
from ..mixins import AjaxDeleteMixin, AjaxFormMixin
from ..permissions import StaffRequiredMixin, SuperuserRequiredMixin


class CategoryListView(StaffRequiredMixin, ListView):
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.order_by('name')


class CategoryCreateView(AjaxFormMixin, StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/categories/form.html'
    partial_template_name = 'dashboard/categories/_form_fields.html'
    success_url = reverse_lazy('dashboard:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء القسم "{self.object.name}".')
        return response


class CategoryUpdateView(AjaxFormMixin, StaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/categories/form.html'
    partial_template_name = 'dashboard/categories/_form_fields.html'
    success_url = reverse_lazy('dashboard:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث القسم "{self.object.name}".')
        return response


class CategoryDeleteView(AjaxDeleteMixin, SuperuserRequiredMixin, DeleteView):
    model = Category
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:category_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'حذف "{self.object.name}"؟'
        if self.object.products.exists():
            ctx['warning'] = (
                f'لا يزال هذا القسم يحتوي على {self.object.products.count()} منتج. '
                'انقلها أو احذفها أولاً — لا يمكن حذف الأقسام المستخدَمة.'
            )
        ctx['cancel_url'] = reverse_lazy('dashboard:category_list')
        return ctx
