from django.shortcuts import get_object_or_404
from rest_framework.response import Response
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

  #  title = models.CharField(max_length=100, unique=True)
  #   content = models.TextField(max_length=2000)
  #   created_at = models.DateField(auto_now_add=True)
  #   links = models.CharField(blank=True)
  #   TAGS = [
  #       ('personal', 'Personal'),
  #       ('rug_making','Rug Making'),
  #       ('inspiration', 'Inspiration'),
  #       ('events', 'Events')
  #   ]
  #   tags =