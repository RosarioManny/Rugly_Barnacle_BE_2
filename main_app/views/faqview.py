from rest_framework import generics
from ..models import FaqModel
from ..serializers import FaqSerializer

class FaqList(generics.ListAPIView):
  queryset = FaqModel.objects.all()
  serializer_class = FaqSerializer