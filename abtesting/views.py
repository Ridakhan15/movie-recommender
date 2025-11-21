# abtesting/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from .models import AlgorithmPerformance, AlgorithmComparison

@login_required
def abtesting_dashboard(request):
    """
    “Main” view for A/B‑testing UI.

    We already have a template at
        recommender/templates/admin/ab_testing_dashboard.html
    So we can simply render that template from here.
    """
    return render(request, 'admin/ab_testing_dashboard.html')

@login_required
def algorithm_performance_dashboard(request):
    """
    Shows the aggregated performance metrics per algorithm.
    """
    comparison = AlgorithmComparison.objects.filter(is_active=True).first()

    performances = AlgorithmPerformance.objects.none()
    algorithm_stats = {}

    if comparison:
        performances = AlgorithmPerformance.objects.filter(comparison=comparison)

        for algo in ['collaborative', 'svd', 'content', 'hybrid']:
            algo_performances = performances.filter(algorithm=algo)
            if algo_performances.exists():
                stats = algo_performances.aggregate(
                    avg_rating=Avg('average_rating'),
                    avg_time=Avg('response_time'),
                    avg_diversity=Avg('diversity_score'),
                    total_users=Count('user', distinct=True),
                    total_tests=Count('id')
                )
                algorithm_stats[algo] = stats
            else:
                algorithm_stats[algo] = {
                    'avg_rating': 0.0,
                    'avg_time': 0.0,
                    'avg_diversity': 0.0,
                    'total_users': 0,
                    'total_tests': 0,
                }

    return render(request, 'abtesting/performance_dashboard.html', {
        'algorithm_stats': algorithm_stats,
        'performances': performances,
        'comparison': comparison,
    })
