#!/bin/bash
set -e

echo "🔄 Waiting for MongoDB to be ready..."

# Wait for MongoDB
until mongosh --host mongodb --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  echo "⏳ Waiting for MongoDB..."
  sleep 2
done

echo "✅ MongoDB is ready!"

# Run CSV to MongoDB migration
echo "📦 Running CSV to MongoDB migration..."
python3 /app/scripts/migrate_to_mongodb.py

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Start Flask application
echo "🚀 Starting Flask application..."
exec python3 run.py
