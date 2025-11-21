from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from recommender.models import Movie, Rating
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
import urllib.request
import zipfile


class Command(BaseCommand):
    help = 'Load MovieLens 100k dataset and train recommendation model'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data loading process...')
        
        # Download MovieLens 100k dataset
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        
        dataset_url = 'https://files.grouplens.org/datasets/movielens/ml-100k.zip'
        zip_path = os.path.join(data_dir, 'ml-100k.zip')
        extract_path = os.path.join(data_dir, 'ml-100k')
        
        if not os.path.exists(extract_path):
            self.stdout.write('Downloading MovieLens 100k dataset...')
            urllib.request.urlretrieve(dataset_url, zip_path)
            
            self.stdout.write('Extracting dataset...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(data_dir)

# FIX: Detect double-folder structure
            if not os.path.exists(extract_path):
                inner_folder = os.path.join(data_dir, 'ml-100k', 'ml-100k')
                if os.path.exists(inner_folder):
                    os.rename(inner_folder, extract_path)
            
            os.remove(zip_path)
            self.stdout.write(self.style.SUCCESS('Dataset downloaded and extracted!'))
        else:
            self.stdout.write('Dataset already exists.')
        
        # Load movies
        self.stdout.write('Loading movies...')
        movies_file = os.path.join(extract_path, 'u.item')
        
        movies_data = []
        with open(movies_file, 'r', encoding='latin-1') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    movie_id = int(parts[0])
                    title = parts[1]
                    # Extract genres (last 19 columns are genre indicators)
                    genres_list = []
                    genre_names = ['unknown', 'Action', 'Adventure', 'Animation', 
                                   'Children', 'Comedy', 'Crime', 'Documentary', 'Drama',
                                   'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery',
                                   'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
                    
                    if len(parts) >= 24:
                        for i, genre_flag in enumerate(parts[5:24]):
                            if genre_flag == '1' and i < len(genre_names):
                                genres_list.append(genre_names[i])
                    
                    genres = '|'.join(genres_list) if genres_list else 'Unknown'
                    movies_data.append({'movie_id': movie_id, 'title': title, 'genres': genres})
        
        # Create movies in database
        Movie.objects.all().delete()
        movies_to_create = [Movie(**movie_data) for movie_data in movies_data]
        Movie.objects.bulk_create(movies_to_create, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(movies_data)} movies'))
        
        # Load ratings
        self.stdout.write('Loading ratings...')
        ratings_file = os.path.join(extract_path, 'u.data')
        
        ratings_df = pd.read_csv(
            ratings_file,
            sep='\t',
            names=['user_id', 'movie_id', 'rating', 'timestamp'],
            encoding='latin-1'
        )
        
        self.stdout.write(f'Total ratings in dataset: {len(ratings_df)}')
        
        # Create sample users and load their ratings
        self.stdout.write('Creating sample users...')
        Rating.objects.all().delete()
        
        # Get unique user IDs from the dataset
        unique_users = ratings_df['user_id'].unique()[:50]  # Use first 50 users as sample
        
        for user_id in unique_users:
            username = f'user{user_id}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'password': 'pbkdf2_sha256$260000$temp$temppassword'}
            )
            
            if created:
                user.set_password('password123')
                user.save()
            
            # Get ratings for this user
            user_ratings = ratings_df[ratings_df['user_id'] == user_id]
            
            ratings_to_create = []
            for _, row in user_ratings.iterrows():
                try:
                    movie = Movie.objects.get(movie_id=row['movie_id'])
                    ratings_to_create.append(
                        Rating(user=user, movie=movie, rating=row['rating'])
                    )
                except Movie.DoesNotExist:
                    continue
            
            if ratings_to_create:
                Rating.objects.bulk_create(ratings_to_create, batch_size=500)
        
        self.stdout.write(self.style.SUCCESS(f'Created {User.objects.count()} sample users'))
        self.stdout.write(self.style.SUCCESS(f'Loaded {Rating.objects.count()} ratings'))
        
        # Train recommendation model
        self.stdout.write('Training recommendation model...')
        
        # Create user-item matrix
        all_ratings = Rating.objects.select_related('user', 'movie').all()
        
        # Build the matrix
        user_ids = list(User.objects.values_list('id', flat=True))
        movie_ids = list(Movie.objects.values_list('movie_id', flat=True))
        
        # Create mapping dictionaries
        user_id_to_idx = {user_id: idx for idx, user_id in enumerate(user_ids)}
        movie_id_to_idx = {movie_id: idx for idx, movie_id in enumerate(movie_ids)}
        
        # Initialize matrix
        user_item_matrix = np.zeros((len(user_ids), len(movie_ids)))
        
        # Fill matrix with ratings
        for rating in all_ratings:
            user_idx = user_id_to_idx.get(rating.user.id)
            movie_idx = movie_id_to_idx.get(rating.movie.movie_id)
            if user_idx is not None and movie_idx is not None:
                user_item_matrix[user_idx, movie_idx] = rating.rating
        
        # Save model
        os.makedirs('ml_models', exist_ok=True)
        model_data = {
            'user_item_matrix': user_item_matrix,
            'user_ids': user_ids,
            'movies_list': movie_ids,
            'user_id_to_idx': user_id_to_idx,
            'movie_id_to_idx': movie_id_to_idx
        }
        
        model_path = os.path.join('ml_models', 'recommender_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        self.stdout.write(self.style.SUCCESS('Model trained and saved successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Data loading complete!'))
        self.stdout.write(self.style.SUCCESS(f'Movies: {Movie.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Users: {User.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Ratings: {Rating.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('='*50))