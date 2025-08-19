from rest_framework import generics
from ..models import Category
from ..serializers import CategorySerializer

# TODO: Create CategoryView - Get a list of all categories - Use for filters and Dropdowns
class CategoryView(generics.ListCreateAPIView):
  queryset = Category.objects.all()
  serializer_class = CategorySerializer
