from django.db import transaction
from rest_framework.response import Response
from rest_framework import generics, status 
from rest_framework.views import APIView
from ..models import Cart, Product, CartItem
from ..serializers import CartSerializer, ItemSerializer

class CartView(generics.RetrieveAPIView):
  serializer_class = CartSerializer

  def get_object(self):

    session_key = self.request.session.session_key # <- Get session for the cart.

    session_is_new = not session_key # <- Check if we need to get a new key
  
    if not session_key: 
      self.request.session.create() # <- Create session for the cart.
      session_key = self.request.session.session_key
    
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    # Create a Cart. Setting it's session_key to the currant one created.

    if session_is_new:
      from django.middleware.csrf import get_token
      get_token(self.request)
      print("Generated new CSRF Token for new session")

    self.request.session.modified = True
    
    return cart
  
  def get(self, request, *args, **kwargs):
    response = super().get(request, *args, **kwargs)

    if hasattr(request, 'session') and request.session.modified:
        request.session.save()
        print(f"💾 Session saved and should be setting cookie")
        
    return response
  
class AddtoCartView(generics.CreateAPIView):
  serializer_class = ItemSerializer

  def create(self, request, *args, **kwargs):
    # Get or create session
    session_key = self.request.session.session_key

    session_is_new = not session_key # <- Check if we need to get a new key
    
    if not session_key:
      self.request.session.save()
      session_key = self.request.session.session_key
      print(f"AddToCart - Created new session: {session_key}")

    if session_is_new:
      from django.middleware.csrf import get_token
      get_token(self.request)
      print(f"AddToCart - Generated new CSRF token")

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
    
    cart_item, created = CartItem.objects.get_or_create( # Check if product already exists in cart. Handling when it's already in cart
      cart=cart,
      product=product,
      defaults={'quantity': requested_quantity}
    )

    if not created:
      new_quantity = cart_item.quantity + requested_quantity
      
      if  new_quantity > product.quantity: # Check if adding requested quantity would exceed availability
          return Response(
              {"error": f"Cannot add {requested_quantity} more. Only {product.quantity - cart_item.quantity} available"},
              status=status.HTTP_400_BAD_REQUEST
          )
      cart_item.quantity = new_quantity
      cart_item.save()

    # Save the cart item
    serializer = self.get_serializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

class RemoveFromCartView(APIView):
  serializer_class = CartSerializer

  def delete(self, request, *args, **kwargs):
      """
      Remove item from cart using cart_item_id.
      Reduces quantity or removes item entirely based on remove_quantity.
      """
      session_key = request.session.session_key
      
      # Validate session
      if not session_key:
        return Response(
          {"error": "No active session or cart found."}, 
          status=status.HTTP_400_BAD_REQUEST  
        )
    
      # Get cart
      try: 
          cart = Cart.objects.get(session_key=session_key)
      except Cart.DoesNotExist:
        return Response(
          {"error": "No active cart found."}, 
          status=status.HTTP_404_NOT_FOUND 
        )
    
      # Get cart_item_id from request
      cart_item_id = request.data.get('cart_item_id')
      if not cart_item_id:
        return Response(
          {"error": "No cart_item_id provided"}, 
          status=status.HTTP_400_BAD_REQUEST
        )
      
      # Get remove_quantity (default to 1)
      try:
        remove_quantity = int(request.data.get('quantity', 1))
        if remove_quantity <= 0:
          remove_quantity = 1
      except (ValueError, TypeError):
        remove_quantity = 1
      
      print(f'🔍 Removing cart_item_id: {cart_item_id} from cart: {cart.id}')
      print(f'🔍 Remove quantity: {remove_quantity}')
      
      try:
        # Get the specific cart item
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        print(f'🔍 Found cart item: ID {cart_item.id}, Product: {cart_item.product.name}, Current Qty: {cart_item.quantity}')
        
        with transaction.atomic():
          # Check if we should remove the entire item or just reduce quantity
          if remove_quantity >= cart_item.quantity:
            # Remove entire item if remove_quantity >= current quantity
            print(f'🗑️ Removing entire item (qty {cart_item.quantity})')
            cart_item.delete()
          else:
            # Reduce quantity if remove_quantity < current quantity
            cart_item.quantity -= remove_quantity
            cart_item.save()
            print(f'📉 Reduced quantity to {cart_item.quantity}')
        
          # Return updated cart
          cart.refresh_from_db()
          serializer = self.get_serializer(cart)
          return Response(serializer.data, status=status.HTTP_200_OK)
              
      except CartItem.DoesNotExist:
        print(f'❌ CartItem {cart_item_id} not found in cart {cart.id}')
        
        # Debug: List available cart items
        cart_items = CartItem.objects.filter(cart=cart)
        available_items = list(cart_items.values('id', 'product__id', 'product__name', 'quantity'))
        print(f'🔍 Available cart items: {available_items}')
        
        return Response(
            {
                "error": "Item not found in cart",
                "available_items": available_items
            }, 
            status=status.HTTP_404_NOT_FOUND
        )
        
      except Exception as e:
        print(f'❌ Error removing item: {str(e)}')
        return Response(
            {"error": f"Failed to remove item: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
class ClearCartView(generics.DestroyAPIView):
  serializer_class = CartSerializer

  def delete(self, request, *args, **kwargs):
    session_key = self.request.session.session_key

    if not session_key:
      return Response(
          {"message": "No active session or cart to clear."}, 
          status=status.HTTP_400_BAD_REQUEST
        )
    try: 
      cart = Cart.objects.get(session_key=session_key)

      cart.items.all().delete() # Delete all items in the cart

      serializer = self.get_serializer(cart)
      return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Cart.DoesNotExist:
      return Response(
          {"message": "No active cart to clear."},
          status=status.HTTP_400_BAD_REQUEST
      )

# ------------------------------------------------------ CARTITEMS ------------------------------------------------------

class CartItemList(generics.ListAPIView):
  serializer_class = ItemSerializer
  lookup_field = 'id'

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
  serializer_class = ItemSerializer
  lookup_field = 'id'

  def get_queryset(self):
    session_key = self.request.session.session_key

    if not session_key: # If no session is available, set to an empty object. No crash/error
      return CartItem.objects.none()
      

    return CartItem.objects.filter(cart__session_key=session_key) # filter cart items in the current user's cart
    
  
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