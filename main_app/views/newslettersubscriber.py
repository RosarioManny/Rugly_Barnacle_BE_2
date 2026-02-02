from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import NewsletterSubscriberSerializer
from ..models import NewsletterSubscriber
from rest_framework import status

class NewsletterSubscribeView(APIView):

    # Createing a new serializer instance
    def post(self, request):
        serializer = self.NewsletterSubscriberSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            # Check if the email already exists
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return Response({'message': 'This email is already subscribed.'}, status=status.HTTP_200_OK)
            # Save the new subscriber
            serializer.save()
            return Response({'message': 'Subscription successful!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class NewsletterUnsubscribeView(APIView):
    
    # Delete a subscriber
    def post(self, request):
        email = request.data.get('email')
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            subscriber.delete()
            return Response({'message': 'You have been unsubscribed successfully.'}, status=status.HTTP_200_OK)
        except NewsletterSubscriber.DoesNotExist:
            return Response({'message': 'Email not found in our subscription list.'}, status=status.HTTP_404_NOT_FOUND)