from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.response import Response
from rest_framework import generics, status 
from ..models import Cart, Product, CartItem
from ..serializers import CartSerializer, ItemSerializer

class CartView(generics.RetrieveAPIView):
  serializer_class = CartSerializer

  def get_object(self):

    session_key = self.request.session.session_key
    # Get or create a session for the cart.

    if not session_key:
      self.request.session.save() # Create a session.
      session_key = self.request.session.session_key
    
    
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
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
      return Response({"error": "No product_id is provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Wanted quantity
    requested_quantity = int(request.data.get('quantity', 1)) #Two args. either the specified quantity or default to 1
    
    with transaction.atomic():
      try:
        product = Product.objects.select_for_update().get(id=product_id)
      except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_400_BAD_REQUEST)
      
    if product.quantity < requested_quantity:
      return Response(
          {"error": f"Only {product.quantity} available"}, 
          status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if product already exists in cart. Handling when it's already in cart
    cart_item, created = CartItem.objects.get_or_create(
      cart=cart,
      product=product,
      defaults={'quantity': requested_quantity}
    )

    if not created:
      new_quantity = cart_item.quantity + requested_quantity
      # Check if adding requested quantity would exceed availability
      if  new_quantity > product.quantity:
          return Response(
              {"error": f"Cannot add {requested_quantity} more. Only {product.quantity - cart_item.quantity} available"},
              status=status.HTTP_400_BAD_REQUEST
          )
      cart_item.quantity = new_quantity

    # Save the cart item
    serializer = self.get_serializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# ------------------------------------------------------ CARTITEMS ------------------------------------------------------

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
  serializer_class = ItemSerializer
  lookup_field = 'id'

  def get_queryset(self):
    session_key = self.request.session.session_key

    if not session_key:
      return CartItem.objects.none()
      # If no session is available, set to an empty object. No crash/error

    return CartItem.objects.filter(cart__session_key=session_key)
    # filter cart items in the current user's cart
  
  # SECURITY CODE 
  def get_object(self):
    queryset = self.filter_queryset(self.get_queryset())
    obj = generics.get_object_or_404(queryset, id=self.kwargs["id"])
    return obj
  # This tries to find the object with the given 'id' WITHIN that filtered queryset.
  # If the id isn't in the user's cart, it will naturally return a 404.

"""
NOTES:: 
  < CARTVIEW > 
  get_or_create() returns a tuple (object, created) where:
    - object = is the retrieved or created instance
    - created = is a boolean indicating whether a new object was created

"""