from django.core.management.base import BaseCommand
from recommender.models import Movie, Rating
import numpy as np
import pandas as pd
import pickle
import os

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False


class MovieRatingDataset(Dataset):
    """PyTorch Dataset for movie ratings"""
    def __init__(self, user_ids, movie_ids, ratings):
        self.user_ids = torch.LongTensor(user_ids)
        self.movie_ids = torch.LongTensor(movie_ids)
        self.ratings = torch.FloatTensor(ratings)
    
    def __len__(self):
        return len(self.ratings)
    
    def __getitem__(self, idx):
        return self.user_ids[idx], self.movie_ids[idx], self.ratings[idx]


class NeuralCollaborativeFiltering(nn.Module):
    """Neural Collaborative Filtering Model"""
    def __init__(self, num_users, num_movies, embedding_dim=50, hidden_layers=[64, 32, 16]):
        super(NeuralCollaborativeFiltering, self).__init__()
        
        # Embeddings
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.movie_embedding = nn.Embedding(num_movies, embedding_dim)
        
        # MLP layers
        layers = []
        input_dim = embedding_dim * 2
        
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, 1))
        self.mlp = nn.Sequential(*layers)
    
    def forward(self, user_ids, movie_ids):
        user_emb = self.user_embedding(user_ids)
        movie_emb = self.movie_embedding(movie_ids)
        
        # Concatenate embeddings
        x = torch.cat([user_emb, movie_emb], dim=1)
        
        # Pass through MLP
        output = self.mlp(x)
        return output.squeeze()


class Command(BaseCommand):
    help = 'Train Neural Collaborative Filtering model using PyTorch'

    def handle(self, *args, **kwargs):
        if not PYTORCH_AVAILABLE:
            self.stdout.write(self.style.WARNING('PyTorch not installed. Install with: pip install torch'))
            self.stdout.write(self.style.WARNING('Skipping neural model training...'))
            return
        
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('NEURAL COLLABORATIVE FILTERING TRAINING'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        # Prepare data
        self.stdout.write('\n[1/3] Preparing training data...')
        train_loader, user_map, movie_map, num_users, num_movies = self.prepare_data()
        
        # Train model
        self.stdout.write('\n[2/3] Training neural network...')
        model = self.train_model(train_loader, num_users, num_movies)
        
        # Save model
        self.stdout.write('\n[3/3] Saving model...')
        self.save_model(model, user_map, movie_map)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Neural model training complete!\n'))
    
    def prepare_data(self):
        """Prepare data for neural network training"""
        ratings = Rating.objects.select_related('user', 'movie').all()
        
        user_ids = []
        movie_ids = []
        rating_values = []
        
        for rating in ratings:
            user_ids.append(rating.user.id)
            movie_ids.append(rating.movie.movie_id)
            rating_values.append(rating.rating)
        
        # Create mappings
        unique_users = list(set(user_ids))
        unique_movies = list(set(movie_ids))
        
        user_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
        movie_map = {movie_id: idx for idx, movie_id in enumerate(unique_movies)}
        
        # Map to indices
        user_indices = [user_map[uid] for uid in user_ids]
        movie_indices = [movie_map[mid] for mid in movie_ids]
        
        # Normalize ratings to 0-1
        ratings_normalized = [(r - 1) / 4 for r in rating_values]
        
        # Create dataset and dataloader
        dataset = MovieRatingDataset(user_indices, movie_indices, ratings_normalized)
        train_loader = DataLoader(dataset, batch_size=128, shuffle=True)
        
        self.stdout.write(f'✓ Users: {len(unique_users)}')
        self.stdout.write(f'✓ Movies: {len(unique_movies)}')
        self.stdout.write(f'✓ Ratings: {len(rating_values)}')
        
        return train_loader, user_map, movie_map, len(unique_users), len(unique_movies)
    
    def train_model(self, train_loader, num_users, num_movies, epochs=10):
        """Train the neural network"""
        
        model = NeuralCollaborativeFiltering(num_users, num_movies)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            
            for user_batch, movie_batch, rating_batch in train_loader:
                optimizer.zero_grad()
                
                predictions = model(user_batch, movie_batch)
                loss = criterion(predictions, rating_batch)
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(train_loader)
            self.stdout.write(f'  Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}')
        
        return model
    
    def save_model(self, model, user_map, movie_map):
        """Save the trained model"""
        os.makedirs('ml_models', exist_ok=True)
        
        model_data = {
            'model_state_dict': model.state_dict(),
            'user_map': user_map,
            'movie_map': movie_map,
            'num_users': len(user_map),
            'num_movies': len(movie_map),
        }
        
        with open('ml_models/neural_model.pkl', 'wb') as f:
            pickle.dump(model_data, f)
        
        self.stdout.write(self.style.SUCCESS('✓ Neural model saved to ml_models/neural_model.pkl'))