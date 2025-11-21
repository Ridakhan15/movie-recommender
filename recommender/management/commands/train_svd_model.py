from django.core.management.base import BaseCommand
from recommender.models import Movie, Rating, MovieInteraction
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import pickle
import os


class Command(BaseCommand):
    help = 'Train SVD Matrix Factorization model for better recommendations'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('SVD MATRIX FACTORIZATION TRAINING'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        # Prepare data
        self.stdout.write('\n[1/3] Preparing training data...')
        ratings_df, implicit_df = self.prepare_data()
        
        # Train SVD
        self.stdout.write('\n[2/3] Training SVD model...')
        self.train_svd(ratings_df, implicit_df)
        
        # Summary
        self.stdout.write('\n[3/3] Training complete!')
        self.print_summary()
    
    def prepare_data(self):
        """Prepare explicit ratings and implicit feedback"""
        
        # Explicit ratings
        ratings = Rating.objects.select_related('user', 'movie').all()   # FIXED
        explicit_data = []
        for rating in ratings:
            explicit_data.append({
                'user_id': rating.user.id,
                'movie_id': rating.movie.movie_id,
                'rating': rating.rating
            })
        
        ratings_df = pd.DataFrame(explicit_data)
        print("DEBUG RATING COLUMNS:", ratings_df.columns)
        
        # Implicit feedback (views, watchlist)
        interactions = MovieInteraction.objects.select_related('user', 'movie').all()
        implicit_data = []
        for interaction in interactions:
            weight = 0.5 if interaction.interaction_type == 'watchlist' else 0.3
            implicit_data.append({
                'user_id': interaction.user.id,
                'movie_id': interaction.movie.movie_id,
                'weight': weight
            })
        implicit_df = pd.DataFrame(implicit_data) if implicit_data else pd.DataFrame()
        
        self.stdout.write(f'✓ Explicit ratings: {len(ratings_df)}')
        self.stdout.write(f'✓ Implicit interactions: {len(implicit_df)}')
        
        return ratings_df, implicit_df
    
    def train_svd(self, ratings_df, implicit_df):
        """Train SVD with combined explicit and implicit feedback"""
        
        if ratings_df.empty:
            self.stdout.write(self.style.ERROR("No ratings found. Cannot train SVD model."))
            return
        
        # Create user-movie matrix
        user_movie_matrix = ratings_df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            fill_value=0
        )
        
        # Implicit feedback
        if not implicit_df.empty:
            implicit_matrix = implicit_df.pivot_table(
                index='user_id',
                columns='movie_id',
                values='weight',
                fill_value=0
            )
            implicit_matrix = implicit_matrix.reindex(
                index=user_movie_matrix.index,
                columns=user_movie_matrix.columns,
                fill_value=0
            )
            user_movie_matrix = user_movie_matrix + implicit_matrix
        
        self.stdout.write(f'✓ User-Movie matrix shape: {user_movie_matrix.shape}')
        
        # Apply SVD
        n_components = min(50, min(user_movie_matrix.shape) - 1)
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        
        user_factors = svd.fit_transform(user_movie_matrix)
        movie_factors = svd.components_.T
        
        variance_explained = svd.explained_variance_ratio_.sum()
        self.stdout.write(f'✓ SVD components: {n_components}')
        self.stdout.write(f'✓ Variance explained: {variance_explained:.2%}')
        
        # Save model
        os.makedirs('ml_models', exist_ok=True)
        model_data = {
            'svd': svd,
            'user_factors': user_factors,
            'movie_factors': movie_factors,
            'user_ids': user_movie_matrix.index.tolist(),
            'movie_ids': user_movie_matrix.columns.tolist(),
            'n_components': n_components,
            'variance_explained': variance_explained,
        }
        
        with open('ml_models/svd_model.pkl', 'wb') as f:
            pickle.dump(model_data, f)
        
        self.stdout.write(self.style.SUCCESS('✓ SVD model saved to ml_models/svd_model.pkl'))
    
    def print_summary(self):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('SVD MODEL TRAINING COMPLETE'))
        self.stdout.write('='*70)
        self.stdout.write('✓ Model: ml_models/svd_model.pkl')
        self.stdout.write('✓ Ready for predictions!')
        self.stdout.write('='*70 + '\n')
