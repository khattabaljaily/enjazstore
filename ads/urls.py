from django.urls import path

from . import views

app_name = 'ads'

urlpatterns = [
    path('<int:pk>/click/', views.banner_click, name='click'),
]
