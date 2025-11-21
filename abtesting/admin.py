from django.contrib import admin
from .models import ABTest, ABTestResult, AlgorithmComparison, AlgorithmPerformance

@admin.register(AlgorithmComparison)
class AlgorithmComparisonAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'is_active']

@admin.register(AlgorithmPerformance)
class AlgorithmPerformanceAdmin(admin.ModelAdmin):
    list_display = ['algorithm', 'user', 'num_recommendations', 'average_rating', 'response_time', 'test_date']
    list_filter = ['algorithm', 'test_date']
    search_fields = ['user__username', 'algorithm']
