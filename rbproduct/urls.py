from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
import os

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "message": "Django is running"})

def static_debug(request):
    """Check static files configuration"""
    info = {
        'static_root': settings.STATIC_ROOT,
        'static_url': settings.STATIC_URL,
        'static_root_exists': os.path.exists(settings.STATIC_ROOT),
        'files_in_static_root': os.listdir(settings.STATIC_ROOT) if os.path.exists(settings.STATIC_ROOT) else []
    }
    return JsonResponse(info)

urlpatterns = [ 
    path('admin/', admin.site.urls),
    path('', include('main_app.urls')),
    path('health/', health_check),
    path('static-debug/', static_debug),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)