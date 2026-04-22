from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import NewsletterSubscriberSerializer, NewsletterPostSerializer, NewsletterPostImageSerializer
from ..models import NewsletterSubscriber, NewsletterPost, NewsletterPostImage
from rest_framework import status, generics
from ..services.newletter_service import NewsletterEmailService  
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


# List of all newsletter subscribers (for admin use only)
class NewsletterSubscriberListView(generics.ListAPIView):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer

# Subscribe to the newsletter
class NewsletterSubscribeView(APIView):
    NewsletterSubscriberSerializer = NewsletterSubscriberSerializer
    def post(self, request):
        serializer = self.NewsletterSubscriberSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return Response({'message': 'This email is already subscribed.'}, status=status.HTTP_200_OK)
            serializer.save()
            NewsletterEmailService.send_newsletter_signup_confirmation(email) 
            return Response({'message': 'Subscription successful!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Unsubscribe from the newsletter
@method_decorator(csrf_exempt, name='dispatch')
class NewsletterUnsubscribeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            subscriber.delete()
            return Response({'message': 'You have been unsubscribed successfully.'}, status=status.HTTP_200_OK)
        except NewsletterSubscriber.DoesNotExist:
            return Response({'message': 'Email not found in our subscription list.'}, status=status.HTTP_404_NOT_FOUND)


# ------------------------------------------------ NEWSLETTER POSTS ------------------------------------------------

# Upload an image to an existing post
class NewsletterPostImageUploadView(APIView):
    def post(self, request, post_id):
        try:
            post = NewsletterPost.objects.get(pk=post_id)
        except NewsletterPost.DoesNotExist:
            return Response({'message': 'Newsletter post not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = NewsletterPostImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete a specific image from a post
class NewsletterPostImageDeleteView(APIView):
    def delete(self, request, image_id):
        try:
            image = NewsletterPostImage.objects.get(pk=image_id)
        except NewsletterPostImage.DoesNotExist:
            return Response({'message': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        image.delete()
        return Response({'message': 'Image deleted.'}, status=status.HTTP_204_NO_CONTENT)