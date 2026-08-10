from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from orders.emails import send_return_request_status_update
from orders.models import Order, ReturnRequest

from ..forms import DashboardReturnRequestForm, ReturnRequestStatusForm
from ..mixins import is_ajax
from ..permissions import StaffRequiredMixin


class ReturnRequestListView(StaffRequiredMixin, ListView):
    model = ReturnRequest
    template_name = 'dashboard/returns/list.html'
    context_object_name = 'return_requests'

    def get_queryset(self):
        qs = ReturnRequest.objects.select_related('order').order_by('-created_at')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = ReturnRequest.Status.choices
        ctx['selected_status'] = self.request.GET.get('status', '')
        return ctx


class ReturnRequestDetailView(StaffRequiredMixin, View):
    partial_template_name = 'dashboard/returns/_detail_fields.html'

    def get_object_and_form(self, pk, data=None):
        obj = get_object_or_404(
            ReturnRequest.objects.select_related('order', 'order__user'), pk=pk,
        )
        form = ReturnRequestStatusForm(data, instance=obj)
        return obj, form

    def get(self, request, pk):
        obj, form = self.get_object_and_form(pk)
        context = {'return_request': obj, 'form': form}
        if is_ajax(request):
            return render(request, self.partial_template_name, context)
        return render(request, 'dashboard/returns/detail.html', context)

    def post(self, request, pk):
        obj, form = self.get_object_and_form(pk, data=request.POST)
        previous_status = obj.status
        if form.is_valid():
            form.save()
            if obj.status != previous_status:
                send_return_request_status_update(request, obj)
            if is_ajax(request):
                return JsonResponse({'success': True})
            messages.success(request, f'تم تحديث طلب الإرجاع #{obj.id}.')
            return redirect('dashboard:return_detail', pk=pk)

        if is_ajax(request):
            return render(request, self.partial_template_name, {'return_request': obj, 'form': form}, status=400)
        return redirect('dashboard:return_detail', pk=pk)


class ReturnRequestCreateView(StaffRequiredMixin, View):
    partial_template_name = 'dashboard/returns/_form_fields.html'

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        form = DashboardReturnRequestForm()
        context = {'order': order, 'form': form}
        if is_ajax(request):
            return render(request, self.partial_template_name, context)
        return render(request, 'dashboard/returns/form.html', context)

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        form = DashboardReturnRequestForm(request.POST)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.order = order
            return_request.save()
            if is_ajax(request):
                return JsonResponse({'success': True})
            messages.success(request, f'تم تسجيل طلب الإرجاع للطلب #{order.id}.')
            return redirect('dashboard:order_detail', pk=order.id)

        context = {'order': order, 'form': form}
        if is_ajax(request):
            return render(request, self.partial_template_name, context, status=400)
        return render(request, 'dashboard/returns/form.html', context)
