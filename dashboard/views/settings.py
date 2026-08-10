from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from ..forms import SiteSettingsForm
from ..models import SiteSettings
from ..permissions import ManagerRequiredMixin


class SiteSettingsView(ManagerRequiredMixin, UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'dashboard/settings.html'
    success_url = reverse_lazy('dashboard:settings')

    def get_object(self, queryset=None):
        return SiteSettings.load()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم حفظ الإعدادات.')
        return response
