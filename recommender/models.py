from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils import timezone

# -----------------------------------------------------------
# MOVIE MODEL
# -----------------------------------------------------------

User.add_to_class('following', models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True))


class Movie(models.Model):
    movie_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=500)
    genres = models.CharField(max_length=200, blank=True)
    
    # Content-based fields
    release_year = models.IntegerField(null=True, blank=True)
    director = models.CharField(max_length=200, blank=True)
    cast = models.TextField(blank=True, help_text="Comma-separated cast members")
    plot = models.TextField(blank=True, help_text="Movie plot/synopsis")
    runtime = models.IntegerField(null=True, blank=True, help_text="Runtime in minutes")
    poster_url = models.URLField(blank=True)
    
    # Implicit feedback
    view_count = models.IntegerField(default=0)
    watchlist_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['movie_id']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['movie_id']),
            models.Index(fields=['-view_count']),
            models.Index(fields=['release_year']),
        ]
    
    def __str__(self):
        return f"{self.movie_id}: {self.title}"
    
    @property
    def average_rating(self):
        avg = self.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 0
    
    @property
    def rating_count(self):
        return self.ratings.count()
    
    @property
    def genres_list(self):
        return [g.strip() for g in self.genres.split('|') if g.strip()]
    
    @property
    def cast_list(self):
        return [c.strip() for c in self.cast.split(',') if c.strip()][:5]

    @property
    def comments_list(self):
        return self.comments.all().order_by('-timestamp')


# -----------------------------------------------------------
# RATING MODEL
# -----------------------------------------------------------

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    review_text = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    recommended_by_algorithm = models.CharField(
        max_length=50, 
        blank=True,
        choices=[
            ('collaborative', 'Collaborative Filtering'),
            ('content', 'Content-Based'),
            ('hybrid', 'Hybrid'),
            ('svd', 'SVD Matrix Factorization'),
            ('neural', 'Neural Collaborative Filtering'),
            ('', 'User Discovery'),
        ]
    )
    
    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'movie']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['recommended_by_algorithm']),
        ]
    
    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.rating}"


# -----------------------------------------------------------
# SHARED RECOMMENDATION MODEL
# -----------------------------------------------------------
class MovieList(models.Model):
    LIST_TYPES = [
        ('favorites', 'Favorites'),
        ('watchlist', 'Watchlist'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_lists')
    title = models.CharField(max_length=200)
    list_type = models.CharField(max_length=50, choices=LIST_TYPES, default='custom')
    is_public = models.BooleanField(default=False)
    movies = models.ManyToManyField('Movie', related_name='lists', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"
    
from django.contrib.auth.models import User
from django.db import models

class UserFollow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class SharedRecommendation(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_recommendations')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_recommendations')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    message = models.TextField(blank=True, max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.movie.title}"


# -----------------------------------------------------------
# MOVIE COMMENT MODEL
# -----------------------------------------------------------

class MovieComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_comments')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments')
    comment_text = models.TextField(max_length=1000)
    likes_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['movie', '-timestamp'])]
    
    def __str__(self):
        return f"{self.user.username} on {self.movie.title}"


# -----------------------------------------------------------
# MOVIE INTERACTION
# -----------------------------------------------------------

class MovieInteraction(models.Model):
    INTERACTION_TYPES = [
        ('view', 'Viewed'),
        ('watchlist', 'Added to Watchlist'),
        ('watching', 'Currently Watching'),
        ('watched', 'Finished Watching'),
        ('share', 'Shared'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_interactions')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    watch_progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['movie', 'interaction_type']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.movie.title}"


# -----------------------------------------------------------
# USER PROFILE
# -----------------------------------------------------------

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    favorite_genres = models.CharField(max_length=500, blank=True)
    favorite_directors = models.CharField(max_length=500, blank=True)
    movies_watched_count = models.IntegerField(default=0)
    total_watch_time = models.IntegerField(default=0, help_text="Total minutes watched")
    bio = models.TextField(blank=True, max_length=500)
    avatar_url = models.URLField(blank=True)
    assigned_algorithm = models.CharField(
        max_length=50,
        default='hybrid',
        choices=[
            ('collaborative', 'Collaborative Filtering'),
            ('content', 'Content-Based'),
            ('hybrid', 'Hybrid'),
            ('svd', 'SVD Matrix Factorization'),
            ('neural', 'Neural Collaborative Filtering'),
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.user.username}"
    
    @property
    def favorite_genres_list(self):
        return [g.strip() for g in self.favorite_genres.split(',') if g.strip()]
    
    def update_favorite_genres(self):
        ratings = Rating.objects.filter(user=self.user, rating__gte=4).select_related('movie')
        genre_counts = {}
        for rating in ratings:
            for genre in rating.movie.genres_list:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        self.favorite_genres = ', '.join([genre for genre, _ in top_genres])
        self.movies_watched_count = Rating.objects.filter(user=self.user).count()
        self.save()


# -----------------------------------------------------------
# USER FOLLOW
# -----------------------------------------------------------



# -----------------------------------------------------------
# RECOMMENDATION EXPERIMENT
# -----------------------------------------------------------

class RecommendationExperiment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments')
    algorithm_variant = models.CharField(max_length=50)
    recommendations_shown = models.IntegerField(default=0)
    recommendations_clicked = models.IntegerField(default=0)
    recommendations_rated = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    avg_rating_given = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'algorithm_variant')
    
    def update_metrics(self):
        if self.recommendations_shown > 0:
            self.ctr = (self.recommendations_clicked / self.recommendations_shown) * 100
            self.conversion_rate = (self.recommendations_rated / self.recommendations_shown) * 100
        ratings = Rating.objects.filter(user=self.user, recommended_by_algorithm=self.algorithm_variant)
        if ratings.exists():
            self.avg_rating_given = ratings.aggregate(Avg('rating'))['rating__avg']
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.algorithm_variant}"


# -----------------------------------------------------------
# MODEL UPDATE TASK
# -----------------------------------------------------------

class ModelUpdateTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task_type = models.CharField(max_length=50, default='incremental_update')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    triggered_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    triggered_by_rating = models.ForeignKey(Rating, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task_type} - {self.status}"
