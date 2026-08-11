import threading

from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from ..market_insights import run_market_analysis
from ..models import MarketInsightReport
from ..permissions import ManagerRequiredMixin


class MarketInsightListView(ManagerRequiredMixin, ListView):
    model = MarketInsightReport
    template_name = 'dashboard/market_insights/list.html'
    context_object_name = 'reports'
    paginate_by = 20


class MarketInsightGenerateView(ManagerRequiredMixin, View):
    def post(self, request):
        existing = MarketInsightReport.objects.filter(
            status__in=[MarketInsightReport.Status.PENDING, MarketInsightReport.Status.RUNNING],
        ).first()
        if existing:
            return redirect('dashboard:market_insight_detail', pk=existing.pk)

        report = MarketInsightReport.objects.create(created_by=request.user)
        threading.Thread(target=run_market_analysis, args=(report,), daemon=True).start()
        return redirect('dashboard:market_insight_detail', pk=report.pk)


class MarketInsightDetailView(ManagerRequiredMixin, View):
    def get(self, request, pk):
        report = get_object_or_404(MarketInsightReport, pk=pk)
        return render(request, 'dashboard/market_insights/detail.html', {'report': report})
