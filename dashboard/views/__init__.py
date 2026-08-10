from .analytics import VisitorAnalyticsView
from .banners import BannerCreateView, BannerDeleteView, BannerListView, BannerUpdateView
from .categories import CategoryCreateView, CategoryDeleteView, CategoryListView, CategoryUpdateView
from .coupons import CouponCreateView, CouponDeleteView, CouponListView, CouponUpdateView
from .customers import CustomerDetailView, CustomerListView
from .employees import (
    EmployeeCreateView,
    EmployeeListView,
    EmployeeSetPasswordView,
    EmployeeToggleActiveView,
    EmployeeUpdateView,
)
from .home import DashboardHomeView
from .marketing import MarketingEmailView
from .orders import OrderBillView, OrderDeleteView, OrderDetailView, OrderListView, PaymentConfirmView
from .products import ProductDeleteView, ProductFormView, ProductListView
from .reports import ReportsExportView, ReportsView
from .returns import ReturnRequestCreateView, ReturnRequestDetailView, ReturnRequestListView
from .reviews import ReviewDetailView, ReviewListView
from .settings import SiteSettingsView
from .stock_value import StockValueReportView

__all__ = [
    'DashboardHomeView',
    'VisitorAnalyticsView',
    'ProductListView', 'ProductFormView', 'ProductDeleteView',
    'CategoryListView', 'CategoryCreateView', 'CategoryUpdateView', 'CategoryDeleteView',
    'OrderListView', 'OrderDetailView', 'OrderDeleteView',
    'ReturnRequestListView', 'ReturnRequestDetailView', 'ReturnRequestCreateView',
    'EmployeeListView', 'EmployeeCreateView', 'EmployeeUpdateView', 'EmployeeToggleActiveView', 'EmployeeSetPasswordView',
    'ReportsView', 'ReportsExportView',
    'SiteSettingsView',
    'StockValueReportView',
    'CustomerListView', 'CustomerDetailView',
    'BannerListView', 'BannerCreateView', 'BannerUpdateView', 'BannerDeleteView',
    'CouponListView', 'CouponCreateView', 'CouponUpdateView', 'CouponDeleteView',
    'ReviewListView', 'ReviewDetailView',
    'MarketingEmailView',
]
