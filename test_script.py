# test_cloudinary.py
import os
import django
import cloudinary.uploader

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rbproduct.settings')
django.setup()

# Test upload
try:
    result = cloudinary.uploader.upload(
        "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        public_id="test_upload"
    )
    print("✓ Cloudinary upload successful!")
    print(f"URL: {result['url']}")
except Exception as e:
    print(f"✗ Cloudinary error: {e}")