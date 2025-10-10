# CUSTOM ORDER VIEWS
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from ..models import CustomOrder, CustomOrderImage
from ..serializers import CustomOrderSerializer
from ..services.email_service import OrderEmailService  

class CustomOrderView(generics.ListCreateAPIView):
    queryset = CustomOrder.objects.all().order_by('-created_at')
    serializer_class = CustomOrderSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminUser()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        # Handle file uploads separately
        images_data = request.FILES.getlist('images')
        
        # Create the custom order first
        order_serializer = self.get_serializer(data=request.data)
        order_serializer.is_valid(raise_exception=True)
        custom_order = order_serializer.save()
        
        # Handle image uploads
        for image_data in images_data:
            CustomOrderImage.objects.create(custom_order=custom_order, image=image_data)
        
        # Refresh the order from database to ensure we have the latest data including images
        custom_order.refresh_from_db()
        
        print("New Custom order: ", order_serializer.data)
        
        # SEND EMAILS AFTER ORDER AND IMAGES ARE SAVED
        try:
            OrderEmailService.send_order_notification(custom_order)
            OrderEmailService.send_order_confirmation(custom_order)
            print("Emails sent successfully!")
        except Exception as e:
            print(f"Error sending emails: {e}")
            # Don't fail the order creation if emails fail
        
        headers = self.get_success_headers(order_serializer.data)
        return Response(
            order_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
class CustomOrderDetailView(generics.RetrieveAPIView):
    serializer_class = CustomOrderSerializer
    lookup_field = 'reference_id'
    queryset = CustomOrder.objects.all()
    permission_classes = [AllowAny]
    filter_backends = []