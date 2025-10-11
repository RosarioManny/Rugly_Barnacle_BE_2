import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("=== Starting Django Debug ===")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rbproduct.settings')
    print("✓ DJANGO_SETTINGS_MODULE set")
    
    # Try to import Django
    import django
    print("✓ Django imported")
    
    # Try to configure Django
    django.setup()
    print("✓ django.setup() completed")
    
    # Try to import settings
    from django.conf import settings
    print("✓ Django settings imported")
    print(f"✓ DEBUG = {settings.DEBUG}")
    print(f"✓ ALLOWED_HOSTS = {settings.ALLOWED_HOSTS}")
    
    # Try to import WSGI application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("✓ WSGI application created successfully")
    
    print("=== Django Debug Complete - App Should Work ===")
    
except Exception as e:
    print("✗ ERROR during setup:")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
    traceback.print_exc()
    sys.exit(1)