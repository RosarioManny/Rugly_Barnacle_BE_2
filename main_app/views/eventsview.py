from rest_framework import generics, filters
from ..models import Event
from ..serializers import EventSerializer

class EventList(generics.ListCreateAPIView):
  queryset = Event.objects.all().order_by('-start_time')
  serializer_class = EventSerializer
  filter_backends = [filters.SearchFilter]
  search_fields = ['title', 'location', 'event_type', 'start_time', 'event_type']

class EventListDetails(generics.RetrieveUpdateDestroyAPIView):
  queryset = Event.objects.all()
  serializer_class = EventSerializer
  lookup_field = 'id'