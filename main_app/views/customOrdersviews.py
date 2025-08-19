from rest_framework.response import Response
from rest_framework import generics, status 
from ..models import CustomOrder
from ..serializers import CustomOrderSerializer

class CustomOrderView(generics.ListCreateAPIView):
  queryset = CustomOrder.objects.all()
  serializer_class = CustomOrderSerializer

  # Create the custom Order
  def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception = True)
    self.perform_create(serializer)

    # TODO:: NOT YET MADE - Send notification funtion
    # send_order_notification(serializer.data)
    print(serializer.data)

    headers = self.get_success_headers(serializer.data)
    return Response(
        serializer.data,
        status= status.HTTP_201_CREATED,
        headers=headers
      )