from rest_framework.response import Response
from rest_framework import generics, status, permissions
from ..models import CustomOrder
from ..serializers import CustomOrderSerializer

class CustomOrderView(generics.ListCreateAPIView):
  # .order_by('-created_at') allows you to see the most recent in the list
  queryset = CustomOrder.objects.all().order_by('-created_at')
  serializer_class = CustomOrderSerializer
  
  # CONTROL PERMISSIONS
  def get_permissions(self):
    if self.request.method == 'GET':
      # Check if admin
      return [permissions.IsAdminUser()]
    elif self.request.method == 'POST':
      # Anyone can create a post
      return [permissions.AllowAny()]
    return super().get_permissions()
  
  # Create the custom Order
  def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception = True)
    self.perform_create(serializer)

    # TODO:: NOT YET MADE - Send email notification funtion
    # send_order_notification(serializer.data)
    print("New Custom order: ",serializer.data)

    headers = self.get_success_headers(serializer.data)
    return Response(
        serializer.data,
        status= status.HTTP_201_CREATED,
        headers=headers
      )

class CustomOrderDetailView(generics.RetrieveAPIView):
  serializer_class = CustomOrder
  lookup_field = 'reference_id'
  queryset = CustomOrder.objects.all()
  permission_classe = [permissions.AllowAny()]  