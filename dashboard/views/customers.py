from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView

from ..mixins import is_ajax
from ..permissions import ManagerRequiredMixin

User = get_user_model()


class CustomerListView(ManagerRequiredMixin, ListView):
    template_name = 'dashboard/customers/list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        return User.objects.filter(is_staff=False).order_by('-last_seen_at', '-date_joined')


class CustomerDetailView(ManagerRequiredMixin, View):
    partial_template_name = 'dashboard/customers/_detail_fields.html'

    def get(self, request, pk):
        customer = get_object_or_404(User, pk=pk, is_staff=False)
        orders = customer.orders.prefetch_related('items').order_by('-created_at')
        context = {'customer': customer, 'orders': orders}
        if is_ajax(request):
            return render(request, self.partial_template_name, context)
        return render(request, 'dashboard/customers/detail.html', context)
