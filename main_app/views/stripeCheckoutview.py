import json
import os
import stripe
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from ..serializers import CartSerializer
from ..models import Cart, CartItem, Product

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class CreateCheckoutSessionView(APIView):
    serializer_class = CartSerializer

    def get(self, request):
        return Response({'message': 'POST to this endpoint to create checkout session'})
    
    def calc_shipping_cost(self, cart, local_quantities=None):
        total_price = 0
        for item in cart.items.all():
            if local_quantities:
                quantity = local_quantities.get(str(item.product.id), item.quantity)
            else:
                quantity = item.quantity
            total_price += item.product.price * quantity
                
        # CHECK THE CART IF A CUSTOM ORDER DOWN PAYMENT ITEM EXISTS.
        has_custom_order = cart.items.filter(product__name__icontains='custom order').exists()

        if has_custom_order:
            return 'shr_1SopJ7L7WYX2dlYRclNVVtsB'  # OVER $100 - FREE SHIPPING 
        
        # FIXED LOGIC GAPS
        if total_price < 50:
            return 'shr_1SopKgL7WYX2dlYRpqzOeWNa'  # UNDER $50 - 4.99 SHIPPING 
        elif total_price < 100:  # 50 <= total_price < 100
            return 'shr_1SopHiL7WYX2dlYRLQ7OFx34'  # $50 TO $100 - 7.99 SHIPPING
        else:  # total_price >= 100
            return 'shr_1SopJ7L7WYX2dlYRclNVVtsB'  # OVER $100 - FREE SHIPPING 
    
    def _validate_stock(self, cart, local_quantities=None):
        errors = []
        for item in cart.items.select_related('product'):
            if local_quantities:
                quantity = local_quantities.get(str(item.product.id), item.quantity)
            else:
                quantity = item.quantity

            if quantity > item.product.quantity:
                errors.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'requested': quantity,  # FIXED: CONSISTENT WITH FRONTEND EXPECTATION
                    'available': item.product.quantity,  # FIXED: CONSISTENT WITH FRONTEND EXPECTATION
                })
        return errors
  
    def post(self, request):
        cart = self.get_cart_from_user(request)

        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # GET LOCAL QUANTITIES FROM REQUEST
        local_quantities = request.data.get('local_quantities', {})
        
        # USE THE HELPER METHOD FOR CONSISTENT VALIDATION
        stock_errors = self._validate_stock(cart, local_quantities)
        
        if stock_errors:
            return Response(
                {
                    'error': 'Some items in your cart exceed available stock',
                    'items': stock_errors  # USE 'items' TO MATCH YOUR FRONTEND ERROR HANDLING
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        line_items = []
        for item in cart.items.all():
            if not item.product:
                continue
            
            # USE LOCAL QUANTITY IF PROVIDED, OTHERWISE USE CART QUANTITY
            quantity = local_quantities.get(str(item.product.id), item.quantity)
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price * 100),
                },
                'quantity': quantity,
            })
        
        if not line_items:
            return Response({'error': 'No valid items in cart'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            shipping_rate_id = self.calc_shipping_cost(cart, local_quantities)
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                automatic_tax={'enabled': True},
                customer_email='customer@example.com',
                shipping_options=[{'shipping_rate': shipping_rate_id}],
                shipping_address_collection={
                    'allowed_countries': ['US', 'CA'],
                },
                mode='payment',
                success_url=f'http://localhost:5173/checkout/success?session_id={{CHECKOUT_SESSION_ID}}&cart_id={cart.id}',
                cancel_url='http://localhost:5173/checkout/cancel',
                metadata={
                    'cart_id': str(cart.id),
                    'local_quantities': json.dumps(local_quantities),
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

    def _verify_stripe_session(self, session_id):
        try: 
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status != 'paid':
                raise ValueError(f"Payment status is {session.payment_status}, not 'paid'")
            return session
        except stripe.error.StripeError as e:
            raise ValueError(f"Invalid Stripe session ID: {str(e)}")

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
            }, status=status.HTTP_200_OK)
        
        try:
            # VERIFY STRIPE SESSION
            stripe_session = self._verify_stripe_session(stripe_session_id)
            # VERIFY USERS CART
            cart = self._validate_cart_access(session_key, stripe_session.metadata.get('cart_id'))
            # RETRIEVE CART ITEMS
            cart_items = CartItem.objects.filter(cart=cart).select_related('product')

            if not cart_items.exists():
                return Response(
                    {
                        'message': 'Empty Cart - No items found in cart',
                        'deducted_items': []
                    },
                    status=status.HTTP_200_OK
                )
            
            deduction_results = self._deduct_product_quantities(cart_items, stripe_session)

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
    
    def _validate_cart_access(self, session_key, cart_id=None):
        """Validate that the user has access to this cart"""
        if cart_id:
            try:
                # VALIDATE CART_ID MATCHES THE USER'S SESSION
                cart = Cart.objects.get(id=cart_id, session_key=session_key)
                return cart
            except Cart.DoesNotExist:
                raise ValueError("Cart ID does not match your session")
        else:
            # FALLBACK TO SESSION LOOKUP
            try:
                return Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                raise ValueError("No cart found for your session")
  
    def _check_and_mark_processed(self, session_id):
        cache_key = f"stripe_session_processed_{session_id}"

        is_processed = cache.get(cache_key)
        print(f"🔍 Checking cache for {cache_key}: {is_processed}")

        if is_processed:
            print(f"⚠️ Session {session_id} already processed!")
            return True
        
        cache.set(cache_key, True, timeout=3600)
        print(f"✅ Marked session {session_id} as processed")
        return False
  
    def _deduct_product_quantities(self, cart_items, stripe_session=None):
        results = []

        local_quantities = {}
        if stripe_session and stripe_session.metadata:
            local_quantities_json = stripe_session.metadata.get('local_quantities')
            if local_quantities_json:
                try:
                    local_quantities = json.loads(local_quantities_json)
                except json.JSONDecodeError:
                    pass
                    
        with transaction.atomic():
            for cart_item in cart_items:
                product = cart_item.product 
                original_quantity = product.quantity
                
                # USE QUANTITY FROM STRIPE METADATA IF AVAILABLE, OTHERWISE FROM CART
                if str(product.id) in local_quantities:
                    quantity_to_deduct = local_quantities[str(product.id)]
                else:
                    quantity_to_deduct = cart_item.quantity
                
                product = Product.objects.select_for_update().get(id=product.id)
                
                if product.quantity < quantity_to_deduct:
                    raise ValueError(  
                        f"Insufficient stock for {product.name}."
                        f"Available: {product.quantity}, Requested: {quantity_to_deduct}"
                    )
                product.quantity -= quantity_to_deduct
                product.save()

                print(f"Deducted {quantity_to_deduct} from {product.name}. Stock: {original_quantity} -> {product.quantity}")
                results.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity_deducted": quantity_to_deduct,
                    "original_stock": original_quantity,
                    "remaining_stock": product.quantity,
                    "price": str(product.price)  
                })
        return results