import stripe
from ..serializers import CartSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import os
from ..models import Cart, CartItem, Product
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class CreateCheckoutSessionView(APIView):
  serializer_class = CartSerializer

  def get(self, request):
    return Response({'message': 'POST to this endpoint to create checkout session'})
  
  def calc_shipping_cost(self, cart):
    total_price = sum(item.product.price * item.quantity for item in cart.items.all())

    if total_price > 300:
      return 'shr_1ScZPk36wcYu7XNJWziRRMHo' #Free Shipping
    elif total_price > 100:
      return 'shr_1ScZOC36wcYu7XNJ9NEdACJD' #Specialty Shipping
    else:
      return 'shr_1ScZNS36wcYu7XNJ42npURh9' #General Shipping
    
  def post(self, request):
    cart = self.get_cart_from_user(request)

    if not cart.items.exists():
      return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    line_items = []
    for item in cart.items.all():

      if not item.product:
        continue

      line_items.append({
        'price_data': {
          'currency': 'usd',
          'product_data': {
            'name': item.product.name,
          },
          'unit_amount': int(item.product.price * 100),
        },
        'quantity': item.quantity,
      })
    
    if not line_items:
      return Response({'error': 'No valid items in cart'}, status=status.HTTP_400_BAD_REQUEST)
    
    
    try:

      shipping_rate_id = self.calc_shipping_cost(cart)

      checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        automatic_tax={'enabled': True},
        customer_email= 'customer@example.com',
        shipping_options=[{'shipping_rate': shipping_rate_id}],
        shipping_address_collection = {
          'allowed_countries': ['US', 'CA'],
        },
        mode='payment',
        # success_url='https://theruglybarnacle.com/checkout/success',
        # cancel_url='https://theruglybarnacle.com/checkout/cancel',
        success_url=f'http://localhost:5173/checkout/success?session_id={{CHECKOUT_SESSION_ID}}&cart_id={cart.id}',
        
        cancel_url='http://localhost:5173/checkout/cancel',
        metadata={
          'cart_id': str(cart.id),
          }
      )

      print(f"Session created. Automatic tax: {checkout_session.get('automatic_tax', {})}")
      return Response({'checkout_url': checkout_session.url})
    except Exception as e:
      return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
  def get_cart_from_user(self, request):
        
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart
  
class SuccessCheckoutView(APIView):

# VERIFY STRIPE SESSION AND DEDUCT PRODUCT QUANTITIES
  def _verify_stripe_session(self, session_id):
    try: 
      session = stripe.checkout.Session.retrieve(session_id)

      if session.payment_status != 'paid':
        raise ValueError(f"Payment status is {session.payment_status}, not 'paid'")
      return session
    except stripe.error.StripeError as e:
      raise ValueError(f"Invalid Stripe session ID: {str(e)}")

# PROCESS SUCCESSFUL CHECKOUT ***
  def post(self, request):
    session_key = request.session.session_key
    stripe_session_id = request.data.get('session_id')

    if not session_key:
      return Response({'error': 'No active session key found'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not stripe_session_id:
      return Response({'error': 'No active stripe session found'}, status=status.HTTP_400_BAD_REQUEST)
    if self._check_and_mark_processed(stripe_session_id):
      return Response({
          "message": "This checkout was already processed",
          "already_processed": True,
          "session_id": stripe_session_id
        }, status=status.HTTP_200_OK
      ) 
  
    try:

      # VERIFY STRIPE SESSION
      stripe_session = self._verify_stripe_session(stripe_session_id)
      #  VERIFY USERS CART
      cart = self._validate_cart_access(session_key, stripe_session.metadata.get('cart_id'))
      # RETREIVE CART ITEMS
      cart_items = CartItem.objects.filter(cart=cart).select_related('product')

     

      if not cart_items.exists():
        return Response(
          {
            'message': 'Empty Cart - No items found in cart',
            'deducted_items': []
          },
          status=status.HTTP_200_OK
        )
      
      deduction_results = self._deduct_product_quantities(cart_items)

      return Response({
        "message": "Stock quantities updated successfully",
        "deduction_results": deduction_results,
        "session_id": stripe_session_id,
        "cart_id": cart.id,
        "timestamp": timezone.now().isoformat(),
        }, status=status.HTTP_200_OK)
    
    except Cart.DoesNotExist:
      return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
      return Response(
        {"error": f"Failed to update quantities: {str(e)}"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
# VALIDATE USER HAS CART ACCESS
  def _validate_cart_access(self, session_key, cart_id=None):
    """Validate that the user has access to this cart"""
    if cart_id:
      try:
        # Validate cart_id matches the user's session
        cart = Cart.objects.get(id=cart_id, session_key=session_key)
        return cart
      except Cart.DoesNotExist:
          raise ValueError("Cart ID does not match your session")
    else:
      # Fallback to session lookup
      try:
        return Cart.objects.get(session_key=session_key)
      except Cart.DoesNotExist:
        raise ValueError("No cart found for your session")
      
  def _check_and_mark_processed(self, session_id):
    cache_key = f"stripe_session_processed_{session_id}"

    if cache.get(cache_key):
      return True
    
    cache.set(cache_key, True, timeout=3600)
    return False
  
# DEDUCT PRODUCT QUANTITIES
  def _deduct_product_quantities(self, cart_items):
    results = []

    with transaction.atomic():
      for cart_item in cart_items:
        product = cart_item.product 
        original_quantity = product.quantity 

        product = Product.objects.select_for_update().get(id=product.id)

        if product.quantity < cart_item.quantity:
          raise ValueError(  
            f"Insufficient stock for {product.name}."
            f"Available: {product.quantity}, Requested: {cart_item.quantity}"
          )
        
        product.quantity -= cart_item.quantity
        product.save()

        print(f"Deducted {cart_item.quantity} from {product.name}. Stock: {original_quantity} -> {product.quantity}")
        results.append({
          "product_id": product.id,
          "product_name": product.name,
          "quantity_deducted": cart_item.quantity,
          "original_stock": original_quantity,
          "remaining_stock": product.quantity,
          "price": str(product.price)  # Convert Decimal to string for JSON
        })
    return results
