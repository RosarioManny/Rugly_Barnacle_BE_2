from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Product, ProductImage
from ..serializers import ProductSerializer

class ProductList(generics.ListCreateAPIView):
  # Shows a list of all available products
  queryset = Product.objects.all().prefetch_related('properties', 'images') # < - These are the properties set in the ProductSerializer
  serializer_class = ProductSerializer
  
  # This adds the filter backedn
  filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

  # Select items with the category Id
  filterset_fields = ['category']

  # How to sort the items. These can be reversed for either desc || asc
  ordering_fields = ['price', 'name', 'created_at' ]  

class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
  # Show the details of the specified single product
  queryset = Product.objects.all().prefetch_related('properties', 'images')
  serializer_class = ProductSerializer
  lookup_field = 'id'
  filter_backends = []

class ProductImage(generics.ListCreateAPIView):
  queryset = ProductImage.objects.all()
  serializer_class = ProductSerializer