from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from recommender.views import (
    login_view,
    register_view,
    dashboard_view,
    profile_self,
    profile,
    follow_user,
    search_users,
    movie_detail,
    get_recommendations,
    
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recommender.urls')),                     # app URLs

    # A/B testing at /ab-testing-admin/
    path('abtesting/', include('abtesting.urls')),             # A/B‑testing URLs

    # Other paths...
    path('', dashboard_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', login_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_self, name='profile_self'),
    path('profile/<int:user_id>/', profile, name='profile'),
    path('follow/<int:user_id>/', follow_user, name='follow_user'),
    path('search/', search_users, name='search_users'),  # Added for NoReverseMatch fix
    path('movies/<int:movie_id>/', movie_detail, name='movie_detail'),

    path('api/recommendations/', get_recommendations, name='api_recommendations'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
