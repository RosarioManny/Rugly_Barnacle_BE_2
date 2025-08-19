from rest_framework import generics
from ..models import Property
from ..serializers import PropertySerializer

class PropertiesView(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer