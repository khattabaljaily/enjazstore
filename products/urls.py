from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('category/<slug:slug>/', views.product_list, name='list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='detail'),
    path('product/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('product/<slug:slug>/notify-stock/', views.subscribe_stock, name='notify_stock'),
    path('product/<slug:slug>/wishlist-toggle/', views.toggle_wishlist, name='toggle_wishlist'),
]
