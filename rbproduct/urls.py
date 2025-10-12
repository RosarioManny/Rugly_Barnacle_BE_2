from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "message": "Django is running"})

urlpatterns = [ 
    path('admin/', admin.site.urls),
    path('', include('main_app.urls')),
    path('health/', health_check)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)