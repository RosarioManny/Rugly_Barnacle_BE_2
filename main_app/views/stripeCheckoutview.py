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

  def post(self, request):
    cart = self.get_cart_from_user(request)

    line_items = []
    for item in cart.items.all():
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
    
    try:
      checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url='https://theruglybarnacle.com/checkout/success',
        cancel_url='https://theruglybarnacle.com/checkout/cancel',
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