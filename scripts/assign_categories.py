"""
Script to run category assignment for products.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.category_mapper import run_categorization

if __name__ == '__main__':
    dataset_path = 'dataset'
    output_path = 'dataset/product_categories_assigned.csv'
    
    run_categorization(dataset_path, output_path)
