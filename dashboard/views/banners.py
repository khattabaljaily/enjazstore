from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ads.models import Banner

from ..forms import BannerForm
from ..mixins import AjaxDeleteMixin, AjaxFormMixin
from ..permissions import ManagerRequiredMixin, SuperuserRequiredMixin


class BannerListView(ManagerRequiredMixin, ListView):
    template_name = 'dashboard/banners/list.html'
    context_object_name = 'banners'

    def get_queryset(self):
        return Banner.objects.order_by('placement', 'order', '-created_at')


class BannerCreateView(AjaxFormMixin, ManagerRequiredMixin, CreateView):
    model = Banner
    form_class = BannerForm
    template_name = 'dashboard/banners/form.html'
    partial_template_name = 'dashboard/banners/_form_fields.html'
    success_url = reverse_lazy('dashboard:banner_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء البانر "{self.object.name}".')
        return response


class BannerUpdateView(AjaxFormMixin, ManagerRequiredMixin, UpdateView):
    model = Banner
    form_class = BannerForm
    template_name = 'dashboard/banners/form.html'
    partial_template_name = 'dashboard/banners/_form_fields.html'
    success_url = reverse_lazy('dashboard:banner_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث البانر "{self.object.name}".')
        return response


class BannerDeleteView(AjaxDeleteMixin, SuperuserRequiredMixin, DeleteView):
    model = Banner
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:banner_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'حذف "{self.object.name}"؟'
        ctx['cancel_url'] = reverse_lazy('dashboard:banner_list')
        return ctx
