from django.contrib import admin
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required


from .models import (
    Movie, Rating, MovieInteraction, UserProfile,
    UserFollow, MovieComment, SharedRecommendation,
    RecommendationExperiment, ModelUpdateTask, MovieList
)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['movie_id', 'title', 'genres', 'release_year', 'average_rating', 'rating_count', 'view_count', 'watchlist_count']
    search_fields = ['title', 'movie_id', 'director', 'cast']
    list_filter = ['genres', 'release_year']
    ordering = ['movie_id']
    list_per_page = 50
    readonly_fields = ['view_count', 'watchlist_count', 'created_at', 'updated_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'recommended_by_algorithm', 'has_review', 'timestamp']
    search_fields = ['user__username', 'movie__title']
    list_filter = ['rating', 'recommended_by_algorithm', 'timestamp']
    ordering = ['-timestamp']
    list_per_page = 100
    readonly_fields = ['timestamp', 'updated_at']

    def has_review(self, obj):
        return bool(obj.review_text)
    has_review.boolean = True
    has_review.short_description = 'Has Review'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'movie')


@admin.register(MovieInteraction)
class MovieInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'interaction_type', 'watch_progress', 'timestamp']
    search_fields = ['user__username', 'movie__title']
    list_filter = ['interaction_type', 'timestamp']
    ordering = ['-timestamp']
    list_per_page = 100
    readonly_fields = ['timestamp']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'movies_watched_count', 'total_watch_time', 'assigned_algorithm', 'created_at']
    search_fields = ['user__username']
    list_filter = ['assigned_algorithm', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['movies_watched_count', 'created_at', 'updated_at']

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'bio', 'avatar_url')
        }),
        ('Preferences', {
            'fields': ('favorite_genres', 'favorite_directors')
        }),
        ('Statistics', {
            'fields': ('movies_watched_count', 'total_watch_time')
        }),
        ('A/B Testing', {
            'fields': ('assigned_algorithm',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__username', 'following__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(MovieComment)
class MovieCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'comment_preview', 'likes_count', 'timestamp']
    search_fields = ['user__username', 'movie__title', 'comment_text']
    list_filter = ['timestamp']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'updated_at']

    def comment_preview(self, obj):
        return obj.comment_text[:50] + '...' if len(obj.comment_text) > 50 else obj.comment_text
    comment_preview.short_description = 'Comment'


@admin.register(SharedRecommendation)
class SharedRecommendationAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'movie', 'is_read', 'created_at']
    search_fields = ['sender__username', 'receiver__username', 'movie__title']
    list_filter = ['is_read', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(MovieList)
class MovieListAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'list_type', 'is_public', 'movie_count', 'created_at']
    search_fields = ['title', 'user__username']
    list_filter = ['list_type', 'is_public', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    def movie_count(self, obj):
        return obj.movies.count()
    movie_count.short_description = 'Movies'


@admin.register(RecommendationExperiment)
class RecommendationExperimentAdmin(admin.ModelAdmin):
    list_display = ['user', 'algorithm_variant', 'recommendations_shown', 'recommendations_clicked',
                    'recommendations_rated', 'ctr', 'conversion_rate', 'avg_rating_given']
    search_fields = ['user__username', 'algorithm_variant']
    list_filter = ['algorithm_variant', 'created_at']
    ordering = ['-conversion_rate']
    readonly_fields = ['ctr', 'conversion_rate', 'avg_rating_given', 'created_at', 'updated_at']

    fieldsets = (
        ('Experiment Info', {
            'fields': ('user', 'algorithm_variant')
        }),
        ('Raw Metrics', {
            'fields': ('recommendations_shown', 'recommendations_clicked', 'recommendations_rated')
        }),
        ('Calculated Metrics', {
            'fields': ('ctr', 'conversion_rate', 'avg_rating_given')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ModelUpdateTask)
class ModelUpdateTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'task_type', 'status', 'triggered_by_user', 'created_at', 'duration']
    search_fields = ['triggered_by_user__username', 'task_type']
    list_filter = ['status', 'task_type', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'duration']

    def duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return f"{duration.total_seconds():.2f}s"
        return "N/A"
    duration.short_description = 'Duration'

    fieldsets = (
        ('Task Info', {
            'fields': ('task_type', 'status', 'triggered_by_user', 'triggered_by_rating')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'duration')
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


# ------------------------------------------------------------
# SIMPLE GLOBAL ADMIN VIEW — NO ADMIN CLASS OVERRIDING
# ------------------------------------------------------------

# Example A/B testing dashboard view (adjust logic as needed)
@staff_member_required  # Ensures only admin users can access
def abtesting_dashboard(request):
    # Placeholder logic for A/B testing dashboard
    # Replace with your actual A/B testing data/logic (e.g., from models or experiments)
    context = {
        'title': 'A/B Testing Dashboard',
        'experiments': [
            {'name': 'Test 1', 'status': 'Running', 'results': 'Variant A: 60%, Variant B: 40%'},
            {'name': 'Test 2', 'status': 'Completed', 'results': 'Variant A won'},
        ],
        # Add more context like charts, metrics, etc.
    }
    return render(request, 'admin/ab_testing_dashboard.html', context)