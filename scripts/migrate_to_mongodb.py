#!/usr/bin/env python3
"""
MongoDB Migration Script
Migrates CSV data to MongoDB for caching and fast queries
"""
import csv
import os
import sys
from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError

def get_mongo_client():
    """Get MongoDB client from environment or default"""
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/mobile')
    return MongoClient(mongo_uri)

def migrate_products_to_mongodb():
    """Migrate products from CSV to MongoDB"""
    print("🔄 Starting product migration to MongoDB...")
    
    # Connect to MongoDB
    client = get_mongo_client()
    db = client.get_database()
    products_collection = db.products
    
    # Check if data already exists
    existing_count = products_collection.count_documents({})
    if existing_count > 0:
        print(f"✅ MongoDB already has {existing_count} products. Skipping migration.")
        print("   (To force re-migration, manually drop the collection first)")
        return True
    
    # CSV file path
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'products_unified.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found")
        return False
    
    # Read CSV
    products = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert types
                try:
                    row['rating'] = float(row['rating']) if row['rating'] else 0.0
                except:
                    row['rating'] = 0.0
                
                try:
                    row['reviews'] = int(row['reviews']) if row['reviews'] else 0
                except:
                    row['reviews'] = 0
                
                # Add metadata
                row['source'] = 'csv'
                row['last_updated'] = None
                
                products.append(row)
        
        print(f"📊 Read {len(products)} products from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Insert products (don't drop existing collection)
    if products:
        try:
            print(f"💾 Inserting {len(products)} products into MongoDB...")
            result = products_collection.insert_many(products, ordered=False)
            print(f"✅ Inserted {len(result.inserted_ids)} products")
        except BulkWriteError as e:
            print(f"⚠️  Some duplicates skipped: {e.details['nInserted']} inserted")
        except Exception as e:
            print(f"❌ Error inserting products: {e}")
            return False
    
    # Create indexes
    print("🔍 Creating indexes...")
    products_collection.create_index([("product_id", ASCENDING)], unique=True)
    products_collection.create_index([("product_name", ASCENDING)])
    products_collection.create_index([("brand_name", ASCENDING)])
    products_collection.create_index([("primary_category", ASCENDING)])
    products_collection.create_index([("rating", ASCENDING)])
    print("✅ Indexes created")
    
    # Verify
    count = products_collection.count_documents({})
    print(f"✅ Migration complete! Total products in MongoDB: {count}")
    
    return True

def verify_migration():
    """Verify migration was successful"""
    print("\n🔍 Verifying migration...")
    
    client = get_mongo_client()
    db = client.get_database()
    products_collection = db.products
    
    # Check count
    count = products_collection.count_documents({})
    print(f"Total products: {count}")
    
    # Sample product
    sample = products_collection.find_one()
    if sample:
        print(f"\nSample product:")
        print(f"  ID: {sample.get('product_id')}")
        print(f"  Name: {sample.get('product_name')}")
        print(f"  Brand: {sample.get('brand_name')}")
        print(f"  Rating: {sample.get('rating')}")
        print(f"  Category: {sample.get('primary_category')}")
    
    # Check indexes
    indexes = list(products_collection.list_indexes())
    print(f"\nIndexes: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx['name']}")
    
    return count > 0

if __name__ == '__main__':
    try:
        success = migrate_products_to_mongodb()
        if success:
            verify_migration()
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
