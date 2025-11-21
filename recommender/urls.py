from django.contrib import admin
from django.urls import path
from . import views

from recommender.views import (
    login_view, 
    register_view,
    dashboard_view,
    profile_self,
    profile,
    follow_user,
    movie_detail,
    search_users,
    get_recommendations,
    
)
app_name = 'recommender'  # Required for the namespace

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', login_view, name='logout'),  # replace with proper logout view later

    # Dashboard
    path('', dashboard_view, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # User Profiles
    path('profile/', profile_self, name='profile_self'),
    path('profile/<int:user_id>/', profile, name='profile'),

    # Follow
    path('follow/<int:user_id>/', follow_user, name='follow_user'),

    # Movie
    path('movies/<int:movie_id>/', movie_detail, name='movie_detail'),

    # User Search
    path('search-users/', search_users, name='search_users'),

    # API
    path('api/recommendations/', views.get_recommendations, name='api_get_recommendations'),
    path('api/recommendations/click/', views.record_recommendation_click, name='api_record_click'),
    # A/B Testing
    #path('admin/ab-testing/', views.ab_testing_dashboard, name='ab_testing_dashboard'),
]
