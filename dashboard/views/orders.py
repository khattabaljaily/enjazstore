from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, ListView

from orders.emails import send_order_status_update
from orders.models import Order
from payments.registry import get_gateway

from ..forms import OrderStatusForm
from ..mixins import AjaxDeleteMixin, is_ajax
from ..permissions import StaffRequiredMixin, SuperuserRequiredMixin


class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/orders/list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        qs = Order.objects.select_related('user').order_by('-created_at')
        status = self.request.GET.get('status')
        q = self.request.GET.get('q')
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(full_name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Order.Status.choices
        ctx['selected_status'] = self.request.GET.get('status', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class OrderDetailView(StaffRequiredMixin, View):
    partial_template_name = 'dashboard/orders/_detail_fields.html'

    def get_order_and_form(self, pk, data=None):
        order = get_object_or_404(
            Order.objects.select_related('user').prefetch_related('items'), pk=pk,
        )
        form = OrderStatusForm(data, instance=order, user=self.request.user)
        return order, form

    def get(self, request, pk):
        order, form = self.get_order_and_form(pk)
        context = {'order': order, 'form': form}
        if is_ajax(request):
            return render(request, self.partial_template_name, context)
        return render(request, 'dashboard/orders/detail.html', context)

    def post(self, request, pk):
        order, form = self.get_order_and_form(pk, data=request.POST)
        previous_status = order.status
        if form.is_valid():
            form.save()
            if order.status != previous_status:
                send_order_status_update(request, order)
            if is_ajax(request):
                return JsonResponse({'success': True})
            messages.success(request, f'تم تحديث حالة الطلب #{order.id} إلى "{order.get_status_display()}".')
            return redirect('dashboard:order_detail', pk=pk)

        if is_ajax(request):
            return render(request, self.partial_template_name, {'order': order, 'form': form}, status=400)
        return redirect('dashboard:order_detail', pk=pk)


class PaymentConfirmView(StaffRequiredMixin, View):
    """Staff confirms a bank transfer after checking the uploaded receipt.

    Marks the Payment PAID via the gateway's verify_payment() — the only
    place that ever gets called from, since bank transfers have no
    automatic callback to confirm themselves.
    """

    def post(self, request, pk):
        order = get_object_or_404(Order.objects.select_related('payment'), pk=pk)
        if hasattr(order, 'payment') and order.payment.status != order.payment.Status.PAID:
            gateway = get_gateway(order.payment.gateway)
            gateway.verify_payment(order.payment)
            if is_ajax(request):
                return JsonResponse({'success': True})
            messages.success(request, f'تم تأكيد استلام التحويل البنكي للطلب #{order.id}.')
        return redirect('dashboard:order_detail', pk=pk)


class OrderBillView(StaffRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related('user', 'payment').prefetch_related('items'), pk=pk,
        )
        return render(request, 'orders/bill.html', {
            'order': order,
            'subtotal': sum((item.subtotal for item in order.items.all()), start=0),
            'back_url': reverse_lazy('dashboard:order_detail', kwargs={'pk': pk}),
        })


class OrderDeleteView(AjaxDeleteMixin, SuperuserRequiredMixin, DeleteView):
    model = Order
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:order_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'حذف الطلب #{self.object.id}؟'
        ctx['warning'] = 'سيتم حذف الطلب ومنتجاته وسجل الدفع الخاص به نهائيًا.'
        ctx['cancel_url'] = reverse_lazy('dashboard:order_list')
        return ctx
