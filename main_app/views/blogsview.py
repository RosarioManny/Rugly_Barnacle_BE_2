from rest_framework import generics 
from ..models import BlogPost
from ..serializers import BlogSerializer

class BlogList(generics.ListCreateAPIView):
  queryset = BlogPost.objects.all()
  serializer_class = BlogSerializer

class BlogDetails(generics.RetrieveUpdateDestroyAPIView):
  # Show the details of the specified single product
  queryset = BlogPost.objects.all()
  serializer_class = BlogSerializer
  lookup_field = 'id'
  filter_backends = []