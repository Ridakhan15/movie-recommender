from django.core.management.base import BaseCommand
import pickle
import os


class Command(BaseCommand):
    help = 'Create hybrid recommendation system configuration'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('HYBRID RECOMMENDATION SYSTEM CONFIGURATION'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        # Define hybrid weights
        hybrid_config = {
            'weights': {
                'collaborative': 0.35,  # Original collaborative filtering
                'svd': 0.30,            # Matrix factorization
                'content': 0.25,        # Content-based filtering
                'neural': 0.10,         # Neural collaborative filtering
            },
            'fallback_order': ['hybrid', 'svd', 'collaborative', 'content'],
            'min_ratings_for_collaborative': 5,
            'min_ratings_for_svd': 10,
            'enable_implicit_feedback': True,
            'implicit_weight': 0.3,
            'diversity_boost': True,
            'diversity_weight': 0.15,
        }
        
        # Save configuration
        os.makedirs('ml_models', exist_ok=True)
        with open('ml_models/hybrid_config.pkl', 'wb') as f:
            pickle.dump(hybrid_config, f)
        
        self.stdout.write('\n✓ Hybrid configuration created:')
        self.stdout.write(f'  - Collaborative: {hybrid_config["weights"]["collaborative"]*100}%')
        self.stdout.write(f'  - SVD: {hybrid_config["weights"]["svd"]*100}%')
        self.stdout.write(f'  - Content-Based: {hybrid_config["weights"]["content"]*100}%')
        self.stdout.write(f'  - Neural: {hybrid_config["weights"]["neural"]*100}%')
        self.stdout.write(f'  - Implicit Feedback: {"Enabled" if hybrid_config["enable_implicit_feedback"] else "Disabled"}')
        self.stdout.write(f'  - Diversity Boost: {"Enabled" if hybrid_config["diversity_boost"] else "Disabled"}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Configuration saved to ml_models/hybrid_config.pkl\n'))