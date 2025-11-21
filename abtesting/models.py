from django.db import models
from django.contrib.auth.models import User

# Basic A/B Testing Models
class ABTest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    variant_a = models.CharField(max_length=100, default='Original')
    variant_b = models.CharField(max_length=100, default='Variation')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class ABTestResult(models.Model):
    test = models.ForeignKey(ABTest, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.CharField(max_length=20, choices=[('A', 'Variant A'), ('B', 'Variant B')])
    interaction_date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.test.name} - {self.variant} - {self.user.username}"

# Algorithm Performance Testing Models
class AlgorithmComparison(models.Model):
    ALGORITHM_CHOICES = [
        ('collaborative', 'Collaborative Filtering'),
        ('svd', 'SVD Matrix Factorization'),
        ('content', 'Content-Based'),
        ('hybrid', 'Hybrid Approach'),
    ]
    
    name = models.CharField(max_length=100, default="Algorithm Performance Test")
    start_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class AlgorithmPerformance(models.Model):
    comparison = models.ForeignKey(AlgorithmComparison, on_delete=models.CASCADE)
    algorithm = models.CharField(max_length=20, choices=AlgorithmComparison.ALGORITHM_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Performance metrics
    num_recommendations = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    response_time = models.FloatField(default=0.0)
    diversity_score = models.FloatField(default=0.0)
    user_satisfaction = models.IntegerField(default=0)
    
    test_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.algorithm} - {self.user.username}"
