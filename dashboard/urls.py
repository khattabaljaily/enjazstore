from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),

    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/add/', views.ProductFormView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductFormView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/bill/', views.OrderBillView.as_view(), name='order_bill'),
    path('orders/<int:pk>/delete/', views.OrderDeleteView.as_view(), name='order_delete'),
    path('orders/<int:pk>/confirm-payment/', views.PaymentConfirmView.as_view(), name='payment_confirm'),

    path('returns/', views.ReturnRequestListView.as_view(), name='return_list'),
    path('returns/<int:pk>/', views.ReturnRequestDetailView.as_view(), name='return_detail'),
    path('orders/<int:order_id>/returns/add/', views.ReturnRequestCreateView.as_view(), name='return_create'),

    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),

    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('employees/<int:pk>/toggle-active/', views.EmployeeToggleActiveView.as_view(), name='employee_toggle_active'),
    path('employees/<int:pk>/set-password/', views.EmployeeSetPasswordView.as_view(), name='employee_set_password'),

    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),

    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/export/', views.ReportsExportView.as_view(), name='reports_export'),
    path('analytics/', views.VisitorAnalyticsView.as_view(), name='visitor_analytics'),
    path('stock-value/', views.StockValueReportView.as_view(), name='stock_value_report'),

    path('banners/', views.BannerListView.as_view(), name='banner_list'),
    path('banners/add/', views.BannerCreateView.as_view(), name='banner_create'),
    path('banners/<int:pk>/edit/', views.BannerUpdateView.as_view(), name='banner_edit'),
    path('banners/<int:pk>/delete/', views.BannerDeleteView.as_view(), name='banner_delete'),

    path('coupons/', views.CouponListView.as_view(), name='coupon_list'),
    path('coupons/add/', views.CouponCreateView.as_view(), name='coupon_create'),
    path('coupons/<int:pk>/edit/', views.CouponUpdateView.as_view(), name='coupon_edit'),
    path('coupons/<int:pk>/delete/', views.CouponDeleteView.as_view(), name='coupon_delete'),

    path('settings/', views.SiteSettingsView.as_view(), name='settings'),

    path('insights/', views.MarketInsightListView.as_view(), name='market_insight_list'),
    path('insights/generate/', views.MarketInsightGenerateView.as_view(), name='market_insight_generate'),
    path('insights/<int:pk>/', views.MarketInsightDetailView.as_view(), name='market_insight_detail'),

    path('marketing/', views.MarketingEmailView.as_view(), name='marketing'),
]
