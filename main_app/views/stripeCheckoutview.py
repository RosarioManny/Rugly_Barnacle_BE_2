import stripe
from ..serializers import CartSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import os
from ..models import Cart

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class CreateCheckoutSessionView(APIView):
  serializer_class = CartSerializer

  def get(self, request):
    return Response({'message': 'POST to this endpoint to create checkout session'})
  

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
      checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        automatic_tax={'enabled': True},
        customer_email= 'customer@example.com',
        shipping_address_collection = {
          'allowed_countries': ['US', 'CA'],
        },
        mode='payment',
        # success_url='https://theruglybarnacle.com/checkout/success',
        # cancel_url='https://theruglybarnacle.com/checkout/cancel',
        success_url='http://localhost:5173/checkout/success',
        cancel_url='http://localhost:5173/checkout/cancel',
      )
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