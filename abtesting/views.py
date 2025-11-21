from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from .models import AlgorithmPerformance, AlgorithmComparison

@login_required
def algorithm_performance_dashboard(request):
    """Performance dashboard using your existing template"""
    # Get the active comparison
    comparison = AlgorithmComparison.objects.filter(is_active=True).first()
    
    algorithm_stats = {}
    performances = AlgorithmPerformance.objects.none()
    
    if comparison:
        performances = AlgorithmPerformance.objects.filter(comparison=comparison)
        
        # Aggregate data by algorithm
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
                    'total_tests': 0
                }
    
    # Use your existing template
    return render(request, 'admin/ab_testing_dashboard.html', {
        'algorithm_stats': algorithm_stats,
        'performances': performances,
        'comparison': comparison
    })

@login_required
def abtesting_dashboard(request):
    """Main A/B testing dashboard using your existing template"""
    # You can either create a simple template or redirect to performance dashboard
    # For now, let's redirect to the performance dashboard
    return algorithm_performance_dashboard(request)

