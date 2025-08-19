from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status 
from .models import *
from .serializers import *

# Database Home view
class Home(APIView):
  def get(self, request):
    content = {'message': 'Rugly Barncale: Welcome to the Rugly Barnacle Database!'}
    return Response(content)

# ------------------------------------------------------ PRODUCT ------------------------------------------------------

class ProductList(generics.ListCreateAPIView):
  # Shows a list of all available products
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  
  # TODO: Create a method for filtering

class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
  # Show the details of the specified single product
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  lookup_field = 'id'

# ------------------------------------------------------ CART ------------------------------------------------------


# ------------------------------------------------------ CUSTOM ORDER ------------------------------------------------------

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

# TODO: Create CategoryView - Get a list of all categories - Use for filters and Dropdowns
# TODO: Create PropertiesView - Get list of all properties
class PropertiesView(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

"""

NOTES:: 
  < CARTVIEW > 
  get_or_create() returns a tuple (object, created) where:
    - object = is the retrieved or created instance
    - created = is a boolean indicating whether a new object was created

"""