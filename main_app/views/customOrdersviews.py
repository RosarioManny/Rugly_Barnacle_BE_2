# CUSTOM ORDER VIEWS
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from ..models import CustomOrder, CustomOrderImage
from ..serializers import CustomOrderSerializer
from django.core.mail import EmailMessage, send_mail
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
        
    def send_order_notification(self, custom_order):
        try:
            subject = f"RB New Custom Order - #{custom_order.reference_id}"

            html_message = None
            template_paths_to_try = [
                'emails/custom_order_notification.html',
                '../templates/emails/custom_order_notification.html',
                './templates/emails/custom_order_notification.html',
            ]
            
            for path in template_paths_to_try:
                try: 
                    html_message = render_to_string(path, {'order': custom_order})
                    break
                except:
                    continue
            
            if html_message is None: # <- If the html file isn't found. Execute plain text email.
                self.send_plain_text_email(custom_order)
                return
            
            host_email = os.getenv('EMAIL_HOST_USER')
            sender = host_email
            receiver = os.getenv('rosario.emm47@gmail.com')

            email = EmailMessage(
                subject=subject,
                body = html_message,
                from_email=sender,
                to=[receiver], # <- Must be in parathesese becuase EmailMessage is expecting a tuple or list
                reply_to=[custom_order.email]
            )

            email.content_subtype = 'html'
            email.send(fail_silently=False)
            print(f"Order notification email sent for order #{custom_order.reference_id}")
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            self.send_plain_text_email(custom_order)

# Fallback - Plain text custom order email
    def send_plain_text_email(self, custom_order):
        try:
            subject = f"New Order - #{custom_order.reference_id}"
        
            plain_message = f"""
NEW CUSTOM ORDER RECEIVED!

ORDER DETAILS:
──────────────
Reference ID: #{custom_order.reference_id}
Customer Name: {custom_order.customer_name}
Customer Email: {custom_order.email}
Preferred Contact: {custom_order.contact_method.title()}
Contact Info: {custom_order.contact_info or 'Use email above'}

DESIGN DESCRIPTION:
──────────────────
{custom_order.description}

ORDER STATUS:
─────────────
Status: {custom_order.status.title()}
Submitted: {custom_order.created_at}

ACTION REQUIRED:
Review the order details above
Update order status in admin panel
Contact customer within 24-48 hours
Provide quote and timeline
"""
            sender = os.getenv('TEST_EMAIL_HOST_USER')
            receiver = os.getenv('TEST_EMAIL_HOST_USER')
        
            send_mail(
                subject=subject,
                message=plain_message.strip(),
                from_email=sender,
                recipient_list=[receiver],
                reply_to=[custom_order.email],
                fail_silently=False
            )
            print(f"Plain text email sent for order #{custom_order.reference_id}")
            
        except Exception as e:
            print(f"Failed to send plain text email: {e}")
class CustomOrderDetailView(generics.RetrieveAPIView):
    serializer_class = CustomOrderSerializer
    lookup_field = 'reference_id'
    queryset = CustomOrder.objects.all()
    permission_classes = [AllowAny]
    filter_backends = []