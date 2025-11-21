from django.core.management.base import BaseCommand
from recommender.models import Movie
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os


class Command(BaseCommand):
    help = 'Train Content-Based Filtering model using movie metadata'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('CONTENT-BASED FILTERING TRAINING'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        self.stdout.write('\n[1/2] Extracting movie features...')
        movies_data = self.extract_features()

        if not movies_data:
            self.stdout.write(self.style.ERROR("No movies found. Cannot train model."))
            return

        self.stdout.write('\n[2/2] Training content model...')
        self.train_model(movies_data)

        self.stdout.write(self.style.SUCCESS('\n✓ Content-based model training complete!\n'))

    def extract_features(self):
        """Extract textual features from movies"""
        movies = Movie.objects.all()

        movies_data = []
        for movie in movies:

            # Handle null or missing text fields
            genres = movie.genres or ""
            director = movie.director or ""
            cast = movie.cast or ""
            plot = movie.plot or ""

            # Build feature text
            features = f"{genres} {director} {cast} {plot}".strip()

            # If all fields are empty, add fallback text
            if not features.strip():
                features = "unknown movie metadata"

            movies_data.append({
                'movie_id': movie.movie_id,
                'title': movie.title or "",
                'features': features,
                'genres': genres,
            })

        self.stdout.write(f'✓ Extracted features from {len(movies_data)} movies')
        return movies_data

    def train_model(self, movies_data):
        """Train TF-IDF and calculate similarity"""

        # Extract feature list
        features_list = [movie['features'] for movie in movies_data]

        # CHECK: Avoid empty vocabulary error
        if all(len(f.strip()) == 0 for f in features_list):
            self.stdout.write(self.style.ERROR("All movie features are empty. Cannot train TF-IDF."))
            return

        # TFIDF vectorizer tuned to avoid empty vocabulary errors
        tfidf = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000,     # increased for robustness
            min_df=1               # IMPORTANT FIX: let rare words stay
        )

        try:
            tfidf_matrix = tfidf.fit_transform(features_list)
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"TF-IDF failed: {e}"))
            self.stdout.write(self.style.ERROR("Your movie metadata fields may be too empty."))
            return

        # Cosine similarity
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

        self.stdout.write(f'✓ TF-IDF matrix shape: {tfidf_matrix.shape}')
        self.stdout.write(f'✓ Similarity matrix shape: {cosine_sim.shape}')

        # Save model
        os.makedirs('ml_models', exist_ok=True)
        model_data = {
            'tfidf': tfidf,
            'tfidf_matrix': tfidf_matrix,
            'cosine_sim': cosine_sim,
            'movie_ids': [m['movie_id'] for m in movies_data],
            'movie_titles': [m['title'] for m in movies_data],
            'movie_id_to_idx': {m['movie_id']: idx for idx, m in enumerate(movies_data)},
        }

        with open('ml_models/content_model.pkl', 'wb') as f:
            pickle.dump(model_data, f)

        self.stdout.write(self.style.SUCCESS('✓ Content model saved to ml_models/content_model.pkl'))
