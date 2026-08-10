from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<uuid:token>/', views.confirmation, name='confirmation'),
    path('<uuid:token>/', views.order_detail, name='detail'),
    path('<uuid:token>/bill/', views.order_bill, name='bill'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel'),
    path('<int:order_id>/return/', views.request_return, name='request_return'),
]
