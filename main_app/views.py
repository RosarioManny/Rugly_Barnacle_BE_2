from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status 
from .models import *
from .serializers import *

# Database Home view
class Home(APIView):
  def get(self, request):
    content = {'Rugly Barncale: Welcome to the Rugly Barnacle Database!'}
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

class CartView(generics.RetrieveAPIView):
  serializer_class = CartSerializer

  def get_object(self):

    session_key = self.request.session.session_key
    # Get or create a session for the cart.

    if not session_key:
      self.request.session.save() # Create a session.
      session_key = self.request.session.session_key
    
    
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    # Create a Cart. Setting it's session_key to the currant one created.
  
    return cart
  
class AddtoCartView(generics.CreateAPIView):
  serializer_class = ItemSerializer

  def create(self, request, *args, **kwargs):
    # Get or create session
    session_key = self.request.session.session_key
    if not session_key:
      self.request.session.save()
      session_key = request.session.session_key

    # Get or create cart - get_or_create returns a tuple. _ needed
    cart, _ = Cart.objects.get_or_create(session_key=session_key)

    # Validate Product
    product_id = request.data.get('product_id')
    if not product_id:
      return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Wanted quantity
    requested_quantity = int(request.data.get('quantity', 1)) #Two args. either the specified quantity or default to 1
    
    # Attempt to get product
    try: 
      product = get_object_or_404(Product, id=product_id)
      if product.quantity < requested_quantity:
        return Response(
              {"error": f"Only {product.quantity} items available"},
              status=status.HTTP_400_BAD_REQUEST
            )
    except Product.DoesNotExist:
      return Response({"error": "Product not found"}, status=status.HTTP_400_BAD_REQUEST)
    # Check if product already exists in cart. Handling when it's already in cart
    cart_item, created = CartItem.objects.get_or_create(
      cart=cart,
      product=product,
      defaults={'quantity': requested_quantity}
    )

    if not created:
      # Check if adding requested quantity would exceed availability
      if (cart_item.quantity + requested_quantity) > product.quantity:
          return Response(
              {"error": f"Cannot add {requested_quantity} more. Only {product.quantity - cart_item.quantity} available"},
              status=status.HTTP_400_BAD_REQUEST
          )
      cart_item.quantity += requested_quantity
      cart_item.save()

    # Save the cart item
    serializer = self.get_serializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

  
class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
  serializer_class = ItemSerializer

  def get_queryset(self):
    session_key = self.request.session.session_key

    if not session_key:
      return CartItem.objects.none()
      # If no session is available, set to an empty object. No crash/error

    return CartItem.objects.filter(cart__session_key=session_key)
    # filter cart items in the current user's cart


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

# TODO: Create Category 
"""

NOTES:: 
  < CARTVIEW > 
  get_or_create() returns a tuple (object, created) where:
    - object = is the retrieved or created instance
    - created = is a boolean indicating whether a new object was created

"""