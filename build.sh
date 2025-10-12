#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

# Collect static files (force overwrite)
python manage.py collectstatic --no-input --clear

# Apply database migrations
python manage.py migrate

echo "✓ Build completed successfully"