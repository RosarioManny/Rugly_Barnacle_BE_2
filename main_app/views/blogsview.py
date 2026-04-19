from rest_framework import generics, status #type: ignore
from rest_framework.views import APIView #type: ignore
from rest_framework.response import Response #type: ignore
from ..models import BlogPost, Poll, PollChoice, PollVote
from ..serializers import BlogSerializer, PollSerializer, PollVoteSerializer
from main_app import models

class BlogList(generics.ListCreateAPIView):
  queryset = BlogPost.objects.all()
  serializer_class = BlogSerializer

class BlogDetails(generics.RetrieveUpdateDestroyAPIView):
  # Show the details of the specified single product
  queryset = BlogPost.objects.all()
  serializer_class = BlogSerializer
  lookup_field = 'id'
  filter_backends = []


class PollDetailView(generics.RetrieveAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer

class CastVoteView(APIView):
    def post(self, request, pk):
        # Get or create session key to track voter
        if not request.session.session_key:
            request.session.create()
        
        data = {
            'choice': request.data.get('choice'),
            'session_key': request.session.session_key
        }

        serializer = PollVoteSerializer(data=data)
        if serializer.is_valid():
            vote = serializer.save()
            # Increment the vote count on the choice
            PollChoice.objects.filter(pk=vote.choice.pk).update(
                vote_count=models.F('vote_count') + 1
            )
            return Response({'message': 'Vote cast successfully.'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)