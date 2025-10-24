from django.http import JsonResponse
from django.middleware.csrf import get_token 

def Ensure_CSRF(request):
    
    session_key = request.session.session_key
    session_exists_before = bool(session_key)

    if not session_key:
      request.session.create()
      print(f"CSRF Endpoint - Created new session: {request.session.session_key}")
    
    csrf_token = get_token(request)

    response_data = {
      "status": "CSRF Token ensured",
      "session_exists": not session_exists_before,
      "session_key": session_key,
      "csrf_token": csrf_token
      
    }
    return JsonResponse(response_data)