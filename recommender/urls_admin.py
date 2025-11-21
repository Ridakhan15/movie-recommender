from django.urls import path
from .views import abtesting_dashboard

app_name = 'custom_admin'  # Unique namespace
urlpatterns = [
    path('ab-testing/', abtesting_dashboard, name='abtesting_dashboard'),
]