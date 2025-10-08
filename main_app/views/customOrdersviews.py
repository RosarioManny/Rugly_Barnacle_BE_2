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

        self.send_order_notification(custom_order) # Send Form request to Owner
        self.send_order_confirmation(custom_order) # Senf Confirmation to Client
        
        headers = self.get_success_headers(order_serializer.data)
        return Response(
            order_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    # Order Notifcation to owner  
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
            sender = "Rugly Barnacle"
            receiver = os.getenv('TEST_EMAIL_HOST_USER')

            email = EmailMessage(
                subject=subject,
                body = html_message,
                from_email=sender,
                to=[receiver], # <- Must be in [] becuase EmailMessage is expecting a tuple or list
                reply_to=[custom_order.email]
            )

            email.content_subtype = 'html'
            email.send(fail_silently=False)
            print(f"Order notification email sent for order #{custom_order.reference_id}")
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            self.send_plain_text_email(custom_order)

    def send_order_confirmation(self, custom_order):
            
        try:
            subject = f"Custom Order Confirmation - #{custom_order.reference_id}"
            
            # Try HTML template first
            html_message = None
            try:
                html_message = render_to_string('emails/customer_confirmation.html', {
                    'order': custom_order
                })
            except:
                # Fallback to plain text
                pass
            
            if html_message:
                # HTML email
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email="Rugly Barnacle - ",
                    to=[custom_order.email],
                )
                email.content_subtype = "html"
            else:
                # Plain text fallback
                plain_message = f"""
Thank you for your custom order with Rugly Barnacle!

ORDER CONFIRMATION:
──────────────────
Order Reference: #{custom_order.reference_id}
Customer Name: {custom_order.customer_name}
Submitted: {custom_order.created_at.strftime('%B %d, %Y at %I:%M %p')}

WHAT HAPPENS NEXT:
─────────────────
1. I'll review your design request within 24-48 hours
2. You'll receive a quote and timeline for your custom rug
3. Once approved, I'll begin creating your unique piece

DESIGN DETAILS:
───────────────
{custom_order.description}

If you have any questions, simply reply to this email.

Thank you for choosing Rugly Barnacle!
            """
                email = EmailMessage(
                    subject=subject,
                    body=plain_message.strip(),
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[custom_order.email],
                )
            
            email.send(fail_silently=False)
            print(f"Order confirmation sent to customer for order #{custom_order.reference_id}")
            
        except Exception as e:
            print(f"Failed to send customer confirmation: {str(e)}")

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
    def send_order_status_update(self, custom_order):
        """Send status update email to customer"""
        try:
            # Map status to subject lines
            status_subjects = {
                'accepted': f"Order Accepted! - #{custom_order.reference_id}",
                'in_progress': f"Order In Progress! - #{custom_order.reference_id}",
                'completed': f"Order Completed! - #{custom_order.reference_id}",
                'declined': f"Order Update - #{custom_order.reference_id}",
            }
            
            subject = status_subjects.get(custom_order.status, f"Order Update - #{custom_order.reference_id}")
            
            # Try HTML template first
            html_message = None
            try:
                html_message = render_to_string('emails/order_status_update.html', {
                    'order': custom_order
                })
            except:
                # Fallback to plain text
                pass
            
            if html_message:
                # HTML email
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[custom_order.email],
                )
                email.content_subtype = "html"
            else:
                # Plain text fallback
                status_messages = {
                    'accepted': "has been accepted! We'll send payment details shortly.",
                    'in_progress': "is now in progress! Work on your rug has begun.",
                    'completed': "is completed! Your custom rug is ready.",
                    'declined': "could not be accepted at this time.",
                }
                
                plain_message = f"""
Order Status Update

Order Reference: #{custom_order.reference_id}

Hi {custom_order.customer_name},

Your custom rug order {status_messages.get(custom_order.status, 'has been updated.')}

{% if custom_order.admin_notes %}
Update: {custom_order.admin_notes}
{% endif %}

Current Status: {custom_order.status.title()}

If you have any questions, please reply to this email.

Thank you,
The Rugly Barnacle Team
            """
                email = EmailMessage(
                    subject=subject,
                    body=plain_message.strip(),
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[custom_order.email],
                )
            
            email.send(fail_silently=False)
            print(f"Status update email sent for order #{custom_order.reference_id} (Status: {custom_order.status})")
            
        except Exception as e:
            print(f"Failed to send status update email: {str(e)}")
            
class CustomOrderDetailView(generics.RetrieveAPIView):
    serializer_class = CustomOrderSerializer
    lookup_field = 'reference_id'
    queryset = CustomOrder.objects.all()
    permission_classes = [AllowAny]
    filter_backends = []