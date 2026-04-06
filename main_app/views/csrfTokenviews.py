from django.http import JsonResponse
from django.middleware.csrf import get_token, rotate_token

def Ensure_CSRF(request):
    
    session_key = request.session.session_key

    # Create session if none
    if not session_key:
      request.session.create()
      print(f"CSRF Endpoint - Created new session: {request.session.session_key}")

    # Check key is created
    current_session_key = request.session.session_key

    # Check if session key has changed
    stored_session_key = request.session.get('session_key')

    if stored_session_key and stored_session_key != current_session_key:
      rotate_token(request)
      print(f"Session key changed: {stored_session_key} → {current_session_key}")

    request.session['session_key'] = current_session_key
    
    csrf_token = get_token(request)

    response_data = {
      "status": "CSRF Token ensured",
      "session_created": not bool(session_key),
      "session_key": current_session_key,
      "csrf_token": csrf_token
      
    }
    return JsonResponse(response_data)