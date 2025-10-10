from rest_framework import generics 
from ..models import PortfolioImage
from ..serializers import PortfolioSerializer

class PortfolioList(generics.ListAPIView):
  queryset = PortfolioImage.objects.all()
  serializer_class = PortfolioSerializer
