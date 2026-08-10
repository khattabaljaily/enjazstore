from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import FormView

from ..emails import send_marketing_broadcast
from ..forms import MarketingEmailForm
from ..permissions import ManagerRequiredMixin

User = get_user_model()


class MarketingEmailView(ManagerRequiredMixin, FormView):
    form_class = MarketingEmailForm
    template_name = 'dashboard/marketing.html'
    success_url = reverse_lazy('dashboard:marketing')

    def form_valid(self, form):
        recipients = list(
            User.objects.filter(is_staff=False, is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )
        send_marketing_broadcast(
            self.request,
            form.cleaned_data['subject'],
            form.cleaned_data['message'],
            recipients,
        )
        messages.success(self.request, f'تمت جدولة إرسال البريد إلى {len(recipients)} عميل.')
        return super().form_valid(form)
