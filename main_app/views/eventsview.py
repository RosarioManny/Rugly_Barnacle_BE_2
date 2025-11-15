from rest_framework import generics, filters
from ..models import Events
from ..serializers import EventSerializer

class EventList(generics.ListCreateAPIView):
  queryset = Events.objects.all().order_by('-start_time')
  serializer_class = EventSerializer
  filter_backends = [filters.SearchFilters]
  search_fields = ['title', 'location', 'event_type', 'start_time', 'event_type']

class EventListDetails(generics.RetrieveUpdateDestroyAPIView):
  queryset = Events.objects.all()
  serializer_class = EventSerializer
  lookup_field = 'id'