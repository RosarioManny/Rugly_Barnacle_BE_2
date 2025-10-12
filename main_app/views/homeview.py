from rest_framework.views import APIView
from rest_framework.response import Response

class Home(APIView):
    def get(self, request):
        try:
            content = {'message': 'Rugly Barnacle: Welcome to the Rugly Barnacle Database!'}
            return Response(content)
        except Exception as e:
            # Return the error for debugging
            return Response({'error': str(e)}, status=500)