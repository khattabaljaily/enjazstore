from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from products.models import Review

from ..forms import ReviewModerationForm
from ..mixins import is_ajax
from ..permissions import StaffRequiredMixin


class ReviewListView(StaffRequiredMixin, ListView):
    model = Review
    template_name = 'dashboard/reviews/list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        qs = Review.objects.select_related('product', 'user').order_by('-created_at')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Review.Status.choices
        ctx['selected_status'] = self.request.GET.get('status', '')
        return ctx


class ReviewDetailView(StaffRequiredMixin, View):
    partial_template_name = 'dashboard/reviews/_detail_fields.html'

    def get_object_and_form(self, pk, data=None):
        obj = get_object_or_404(Review.objects.select_related('product', 'user'), pk=pk)
        form = ReviewModerationForm(data, instance=obj)
        return obj, form

    def get(self, request, pk):
        obj, form = self.get_object_and_form(pk)
        context = {'review': obj, 'form': form}
        if is_ajax(request):
            return render(request, self.partial_template_name, context)
        return render(request, 'dashboard/reviews/detail.html', context)

    def post(self, request, pk):
        obj, form = self.get_object_and_form(pk, data=request.POST)
        if form.is_valid():
            form.save()
            if is_ajax(request):
                return JsonResponse({'success': True})
            messages.success(request, f'تم تحديث التقييم #{obj.id}.')
            return redirect('dashboard:review_detail', pk=pk)

        if is_ajax(request):
            return render(request, self.partial_template_name, {'review': obj, 'form': form}, status=400)
        return redirect('dashboard:review_detail', pk=pk)
