#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Remove old static files and create fresh directory
rm -rf staticfiles
mkdir -p staticfiles

# Collect static files with verbose output
echo "=== Collecting static files ==="
python manage.py collectstatic --no-input --clear -v 3

# Apply database migrations
echo "=== Running migrations ==="
python manage.py migrate

echo "✓ Build completed successfully"