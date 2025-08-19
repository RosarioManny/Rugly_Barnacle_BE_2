from rest_framework.views import APIView
from rest_framework.response import Response

# Database Home view
class Home(APIView):
  def get(self, request):
    content = {'message': 'Rugly Barncale: Welcome to the Rugly Barnacle Database!'}
    return Response(content)
