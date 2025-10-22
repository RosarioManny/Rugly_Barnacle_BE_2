from django.http import JsonResponse
from django.middleware.csrf import get_token 

def Ensure_CSRF(request):
    """Ensure CSRF token is set in cookies"""
    get_token(request)  # This ensures the token is set
    return JsonResponse({"status": "CSRF token ensured"})