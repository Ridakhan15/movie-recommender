from django.urls import path
from . import views

urlpatterns = [
    path('', views.abtesting_dashboard, name='abtesting_dashboard'),
    path('performance/', views.algorithm_performance_dashboard, name='algorithm_performance'),
]
