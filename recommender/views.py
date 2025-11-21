from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth.models import User
import random
import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .forms import RegisterForm
from .models import (
    UserProfile, UserFollow, Movie, Rating,
    MovieComment, SharedRecommendation,
    RecommendationExperiment
)
import time
from abtesting.models import ABTest, ABTestResult  # Use 'abtesting'

def get_recommendations_view(request):
    start_time = time.time()
    
    # Your existing recommendation logic
    algorithm = request.user.userprofile.assigned_algorithm
    recommendations = generate_recommendations(request.user, algorithm)
    
    end_time = time.time()
    response_time = end_time - start_time
    
    # Track performance in A/B testing
    comparison, created = AlgorithmComparison.objects.get_or_create(
        name="Algorithm Performance Test",
        defaults={'is_active': True}
    )
    
    # Calculate metrics
    avg_rating = calculate_average_rating(recommendations)
    diversity = calculate_diversity(recommendations)
    
    # Save performance data
    AlgorithmPerformance.objects.create(
        comparison=comparison,
        algorithm=algorithm,
        user=request.user,
        num_recommendations=len(recommendations),
        average_rating=avg_rating,
        response_time=response_time,
        diversity_score=diversity
    )
    
    return render(request, 'recommender/recommendations.html', {
        'recommendations': recommendations,
        'algorithm': algorithm
    })


# -----------------------------------------------------------
# USER PROFILE
# -----------------------------------------------------------
@login_required
def profile_self(request):
    """Show logged-in user's own profile."""
    return redirect('profile', user_id=request.user.id)


@login_required
def profile(request, user_id):
    """Show another user's profile or your own."""
    other_user = get_object_or_404(User, id=user_id)

    profile_obj, created = UserProfile.objects.get_or_create(user=other_user)

    follower_count = UserFollow.objects.filter(following=other_user).count()
    following_count = UserFollow.objects.filter(follower=other_user).count()

    is_own_profile = (request.user.id == other_user.id)
    is_following = UserFollow.objects.filter(follower=request.user, following=other_user).exists()
    user_ratings = Rating.objects.filter(user=other_user).select_related('movie')
    movies_rated_count = user_ratings.count()

    top_genres = (
        Rating.objects.filter(user=other_user)
        .values('movie__genres')
        .annotate(count=Count('movie__genres'))
        .order_by('-count')[:5]
    )

    context = {
        "other_user": other_user,
        "profile": profile_obj,
        "profile_user": other_user,
        "follower_count": follower_count,
        "following_count": following_count,
        "is_own_profile": is_own_profile,
        "is_following": is_following,
        "user_ratings": user_ratings,
        "top_genres": top_genres,
        "movies_rated_count": movies_rated_count,
    }

    return render(request, "user_profile.html", context)


# -----------------------------------------------------------
# MOVIE DETAIL
# -----------------------------------------------------------
@login_required
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, movie_id=movie_id)

    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, movie=movie).first()

    similar_movies = Movie.objects.filter(
        genres=movie.genres
    ).exclude(id=movie.id)[:6]

    reviews = MovieComment.objects.filter(movie=movie).order_by('-timestamp')

    context = {
        'movie': movie,
        'user_rating': user_rating,
        'similar_movies': similar_movies,
        'reviews': reviews,
        'average_rating': getattr(movie, 'average_rating', 0),
        'rating_count': getattr(movie, 'rating_count', reviews.count()),
        'comments': getattr(movie, 'comments', []),
    }

    return render(request, 'movie_detail.html', context)


# -----------------------------------------------------------
# USER AUTHENTICATION
# -----------------------------------------------------------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# -----------------------------------------------------------
# DASHBOARD
# -----------------------------------------------------------
@login_required
def dashboard_view(request):
    user_ratings = Rating.objects.filter(user=request.user).select_related('movie')

    if request.method == 'POST':
        movie_id = request.POST.get('movie_id')
        rating_value = request.POST.get('rating')

        if movie_id and rating_value:
            try:
                movie = Movie.objects.get(movie_id=int(movie_id))
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                algorithm = profile.assigned_algorithm or 'hybrid'

                rating_obj, created = Rating.objects.update_or_create(
                    user=request.user,
                    movie=movie,
                    defaults={'rating': int(rating_value), 'recommended_by_algorithm': algorithm}
                )

                try:
                    exp, _ = RecommendationExperiment.objects.get_or_create(
                        user=request.user,
                        algorithm_variant=algorithm
                    )
                    exp.recommendations_rated += 1 if created else 0
                    exp.update_metrics()
                except Exception as e:
                    print(f"[ab-test] failed to update RecommendationExperiment on rating: {e}")

                return redirect('dashboard')
            except (Movie.DoesNotExist, ValueError):
                pass

    search_query = request.GET.get('search', '')
    movies = []
    if search_query:
        movies = Movie.objects.filter(
            Q(title__icontains=search_query) |
            Q(movie_id__icontains=search_query)
        )[:20]

    context = {
        'user_ratings': user_ratings,
        'movies': movies,
        'search_query': search_query,
    }

    return render(request, "dashboard.html", context)


# -----------------------------------------------------------
# FOLLOW USER
# -----------------------------------------------------------
@login_required
def follow_user(request, user_id):
    target = get_object_or_404(User, id=user_id)

    if target == request.user:
        return redirect('profile', user_id=target.id)

    UserFollow.objects.get_or_create(follower=request.user, following=target)
    return redirect('profile', user_id=target.id)


# -----------------------------------------------------------
# SEARCH USERS
# -----------------------------------------------------------
@login_required
def search_users(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)

    return render(request, 'search_users.html', {'query': query, 'results': results})


# -----------------------------------------------------------
# RECOMMENDATION API
# -----------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    user = request.user
    user_ratings = Rating.objects.filter(user=user)

    if not user_ratings.exists():
        return Response({'message': 'Please rate some movies first', 'recommendations': []}, status=status.HTTP_200_OK)

    try:
        model_path = os.path.join('ml_models', 'recommender_model.pkl')

        if not os.path.exists(model_path):
            return Response({'error': 'Model not found. Train model first.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        user_item_matrix = model_data['user_item_matrix']
        movies_list = model_data['movies_list']

        user_ratings_dict = {r.movie.movie_id: r.rating for r in user_ratings}
        user_vector = np.zeros(len(movies_list))

        for idx, movie_id in enumerate(movies_list):
            if movie_id in user_ratings_dict:
                user_vector[idx] = user_ratings_dict[movie_id]

        similarities = cosine_similarity(user_vector.reshape(1, -1), user_item_matrix)[0]
        similar_users_idx = np.argsort(similarities)[::-1]

        recommendations_score = np.zeros(len(movies_list))
        for idx in similar_users_idx[:50]:
            if similarities[idx] > 0:
                recommendations_score += user_item_matrix[idx] * similarities[idx]

        for idx, movie_id in enumerate(movies_list):
            if movie_id in user_ratings_dict:
                recommendations_score[idx] = -1

        top_indices = np.argsort(recommendations_score)[::-1][:10]
        recommended_ids = [movies_list[idx] for idx in top_indices if recommendations_score[idx] > 0]
        movies = Movie.objects.filter(movie_id__in=recommended_ids)

        result = [{'movie_id': m.movie_id, 'title': m.title, 'genres': m.genres} for m in movies]

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.assigned_algorithm:
            profile.assigned_algorithm = random.choice(['collaborative', 'content', 'hybrid'])
            profile.save()

        algorithm = profile.assigned_algorithm

        try:
            exp, _ = RecommendationExperiment.objects.get_or_create(user=user, algorithm_variant=algorithm)
            exp.recommendations_shown += len(result)
            exp.update_metrics()
        except Exception as e:
            print(f"[ab-test] failed to update RecommendationExperiment: {e}")

        return Response({'user_id': user.id, 'username': user.username, 'recommendations': result, 'algorithm': algorithm})

    except Exception as e:
        return Response({'error': f'Error generating recommendations: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------
# RECORD RECOMMENDATION CLICK
# -----------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_recommendation_click(request):
    """
    Expects JSON: { "movie_id": 123, "algorithm": "hybrid" }
    Called when a user clicks a recommended item.
    """
    user = request.user
    movie_id = request.data.get('movie_id')
    algorithm = request.data.get('algorithm', None)

    if not algorithm:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        algorithm = profile.assigned_algorithm or 'hybrid'

    try:
        movie = Movie.objects.get(movie_id=movie_id)
    except Exception:
        return Response({'error': 'movie not found'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        exp, _ = RecommendationExperiment.objects.get_or_create(user=user, algorithm_variant=algorithm)
        exp.recommendations_clicked += 1
        exp.update_metrics()
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[ab-test] failed to record click: {e}")
        return Response({'error': 'failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------
# A/B TESTING DASHBOARD
# -----------------------------------------------------------
#@staff_member_required
#def abtesting_dashboard(request):
    context = {
        'title': 'A/B Testing Dashboard',
        'experiments': [
            {'name': 'Test 1', 'status': 'Running', 'results': 'Variant A: 60%, Variant B: 40%'},
        ],
    }
    return render(request, 'admin/ab_testing_dashboard.html', context)