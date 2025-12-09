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
  
class GetCheckoutSessionView(APIView):
    def get(self, request):
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Retrieve the session from Stripe
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['total_details.breakdown']
            )
            
            # Extract the relevant information
            session_data = {
                'id': session.id,
                'amount_subtotal': session.amount_subtotal,  # In cents
                'amount_total': session.amount_total,        # In cents
                'currency': session.currency.upper(),
                'customer_details': session.customer_details,
                'shipping_options': session.shipping_options,
                'status': session.status,
            }
            
            # Add tax and shipping breakdown if available
            if hasattr(session, 'total_details'):
                session_data['total_details'] = {
                    'amount_shipping': session.total_details.amount_shipping,
                    'amount_tax': session.total_details.amount_tax,
                }
                
                # Add detailed breakdown if expanded
                if hasattr(session.total_details, 'breakdown'):
                    session_data['total_details']['breakdown'] = {
                        'taxes': [
                            {
                                'amount': tax.amount,
                                'rate': {
                                    'display_name': tax.rate.display_name,
                                    'percentage': tax.rate.percentage,
                                }
                            }
                            for tax in session.total_details.breakdown.taxes
                        ] if session.total_details.breakdown.taxes else [],
                        'shipping': session.total_details.breakdown.shipping.amount if session.total_details.breakdown.shipping else 0
                    }
            
            return Response(session_data)
            
        except stripe.error.InvalidRequestError as e:
            return Response(
                {'error': 'Invalid session ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )