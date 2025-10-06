# CUSTOM ORDER VIEWS
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from ..models import CustomOrder, CustomOrderImage
from ..serializers import CustomOrderSerializer
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os

class CustomOrderView(generics.ListCreateAPIView):
    queryset = CustomOrder.objects.all().order_by('-created_at')
    serializer_class = CustomOrderSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminUser()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        # Handle file uploads separately
        images_data = request.FILES.getlist('images')
        
        # Create the custom order first
        order_serializer = self.get_serializer(data=request.data)
        order_serializer.is_valid(raise_exception=True)
        custom_order = order_serializer.save()
        
        # Handle image uploads
        for image_data in images_data:
            CustomOrderImage.objects.create(custom_order=custom_order, image=image_data)
        
        print("New Custom order: ", order_serializer.data)

        self.send_order_notification(custom_order)
        
        headers = self.get_success_headers(order_serializer.data)
        return Response(
            order_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
#     def send_order_notification(self, custom_order):
#         try: 
#             subject = f"New Order - #{custom_order.reference_id}"
            
#             html_message = render_to_string('/emails/custom_order_notification.html', { # < - Two args. The Html file and the dynamic object to populate
#                 'order': custom_order
#             })
#             plain_message = f"""
# NEW CUSTOM ORDER RECEIVED!

# ORDER DETAILS:
# ──────────────
# Reference ID: #{custom_order.reference_id}
# Customer Name: {custom_order.customer_name}
# Customer Email: {custom_order.email}
# Preferred Contact: {custom_order.contact_method.title()}
# Contact Info: {custom_order.contact_info or 'Use email above'}

# DESIGN DESCRIPTION:
# ──────────────────
# {custom_order.description}

# ORDER STATUS:
# ─────────────
# Status: {custom_order.status.title()}
# Submitted: {custom_order.created_at}

# ACTION REQUIRED:
# Review the order details above
# Update order status in admin panel
# Contact customer within 24-48 hours
# Provide quote and timeline
# """
#             osTest = os.getenv('TEST_EMAIL_HOST_USER')
#             print(f"EMAIL > {osTest}")
#             sender = os.getenv('TEST_EMAIL_HOST_USER')
#             receiver = osTest
            
#             email = EmailMessage(
#                 subject=subject,
#                 body=html_message,
#                 from_email=sender,
#                 to=[receiver],
#             )
#             email.content_subtype = "html"

#             email.reply_to = [custom_order.email]
#             email.send(fail_silently=False)
#             print(f"Order notification email sent for order #{custom_order.reference_id}")

#         except Exception as e:
#             print(f"Failed to send email notification: {str(e)}")
            
    def send_order_notification(self, custom_order):
        try: 
            subject = f"New Order - #{custom_order.reference_id}"
            
            # Debug: List all available templates
            from django.template.loader import get_template
            from django.template import TemplateDoesNotExist
            
            print("=== TEMPLATE LOADING DEBUG ===")
            
            # Try to find the template
            try:
                template = get_template('emails/custom_order_notification.html')
                print("✓ Template found using get_template()")
            except TemplateDoesNotExist:
                print("✗ Template not found with get_template()")
                # List what templates are available
                from django.template.loaders.filesystem import Loader
                loader = Loader()
                template_dirs = loader.get_dirs()
                print(f"Template directories: {template_dirs}")
            
            # Try render_to_string with different paths
            template_paths_to_try = [
                'emails/custom_order_notification.html',
                '../templates/emails/custom_order_notification.html',
                './templates/emails/custom_order_notification.html',
            ]
            
            html_message = None
            for path in template_paths_to_try:
                try:
                    html_message = render_to_string(path, {'order': custom_order})
                    print(f"✓ Template found at: {path}")
                    break
                except TemplateDoesNotExist as e:
                    print(f"✗ Template not found at: {path}")
                    continue
            
            if html_message is None:
                print("DEBUG: All template paths failed, using plain text fallback")
                self.send_plain_text_email(custom_order)
                return
            
            print("=============================")
            
            # Rest of your email code...
            sender = os.getenv('TEST_EMAIL_HOST_USER')
            receiver = os.getenv('TEST_EMAIL_HOST_USER')
            
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=sender,
                to=[receiver],
                reply_to=[custom_order.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
            
            print(f"Order notification email sent for order #{custom_order.reference_id}")

        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            import traceback
            traceback.print_exc()

class CustomOrderDetailView(generics.RetrieveAPIView):
    serializer_class = CustomOrderSerializer
    lookup_field = 'reference_id'
    queryset = CustomOrder.objects.all()
    permission_classes = [AllowAny]
    filter_backends = []