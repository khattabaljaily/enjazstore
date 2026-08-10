from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.AccountLoginView.as_view(), name='login'),
    path('logout/', views.AccountLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.my_orders, name='orders'),
    path('wishlist/', views.my_wishlist, name='wishlist'),
    path('password/', views.AccountPasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.AccountPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.AccountPasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'password/reset-confirm/<uidb64>/<token>/',
        views.AccountPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path('password/reset/complete/', views.AccountPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('verify-email/resend/', views.resend_verification, name='resend_verification'),
    path('2fa/setup/', views.two_factor_setup, name='two_factor_setup'),
    path('2fa/disable/', views.two_factor_disable, name='two_factor_disable'),
    path('2fa/verify/', views.two_factor_verify, name='two_factor_verify'),
]
