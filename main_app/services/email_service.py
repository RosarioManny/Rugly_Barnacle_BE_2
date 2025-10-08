# main_app/services/email_service.py
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
import os

class OrderEmailService:
    
    @staticmethod
    def send_order_notification(order):
        """Send notification to owner about new order"""
        try:
            subject = f"RB New Custom Order - #{order.reference_id}"

            html_message = None
            template_paths_to_try = [
                'emails/custom_order_notification.html',
                '../templates/emails/custom_order_notification.html',
                './templates/emails/custom_order_notification.html',
            ]
            
            for path in template_paths_to_try:
                try: 
                    html_message = render_to_string(path, {'order': order})
                    break
                except:
                    continue
            
            if html_message is None: # <- Fallback to plain text
                
                OrderEmailService._send_plain_text_notification(order)
                return
            
            host_email = os.getenv('EMAIL_HOST_USER')
            sender = "Rugly Barnacle"
            receiver = os.getenv('TEST_EMAIL_HOST_USER')

            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=sender,
                to=[receiver],
                reply_to=[order.email]
            )

            email.content_subtype = 'html'
            email.send(fail_silently=False)
            print(f"Order notification email sent for order #{order.reference_id}")
            
        except Exception as e:
            print(f"Failed to send order notification: {str(e)}")
            OrderEmailService._send_plain_text_notification(order)
    
    
    @staticmethod 
    def _send_plain_text_notification(order): # <- FALLBACK EMAIL 
        """Private method for plain text fallback"""
        try:
            subject = f"New Order - #{order.reference_id}"
            plain_message = f"""
NEW CUSTOM ORDER RECEIVED!

ORDER DETAILS:
──────────────
Reference ID: #{order.reference_id}
Customer Name: {order.customer_name}
Customer Email: {order.email}
Preferred Contact: {order.contact_method.title()}
Contact Info: {order.contact_info or 'Use email above'}

DESIGN DESCRIPTION:
──────────────────
{order.description}

ORDER STATUS:
─────────────
Status: {order.status.title()}
Submitted: {order.created_at}

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
                reply_to=[order.email],
                fail_silently=False
            )
            print(f"Plain text email sent for order #{order.reference_id}")

        except Exception as e:
            print(f"Failed to send plain text email: {e}")
    
    @staticmethod
    def send_order_confirmation(order):
        """Send confirmation email to customer"""
        try:
            subject = f"Custom Order Confirmation - #{order.reference_id}"
            
            
            html_message = None
            try:
                html_message = render_to_string('emails/customer_confirmation.html', {
                    'order': order
                })
            except:
                pass  # <- If fail to get html, continue to Fallback to plain text. At this point html_message will remain as None
            
            if html_message: # <- HTML email if found
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[order.email],
                )
                email.content_subtype = "html"
            else: # Plain text fallback if html_message is still None
                plain_message = f"""
Thank you for your custom order with Rugly Barnacle!

ORDER CONFIRMATION:
──────────────────
Order Reference: #{order.reference_id}
Customer Name: {order.customer_name}
Submitted: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}

WHAT HAPPENS NEXT:
─────────────────
1. I'll review your design request within 24-48 hours
2. You'll receive a quote and timeline for your custom rug
3. Once approved, I'll begin creating your unique piece

DESIGN DETAILS:
───────────────
{order.description}

If you have any questions, simply reply to this email.

Thank you for choosing Rugly Barnacle!
                """
                email = EmailMessage(
                    subject=subject,
                    body=plain_message.strip(),
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[order.email],
                )
            
            email.send(fail_silently=False)
            print(f"Order confirmation sent to customer for order #{order.reference_id}")
            
        except Exception as e:
            print(f"Failed to send customer confirmation: {str(e)}")
    
    @staticmethod
    def send_status_update(order, old_status):
        """Send status update email to customer"""
        try:
            
            if old_status == 'pending' and order.status == 'pending': # <- Don't send for initial pending status
                return
                
            # Map status to subject lines
            status_subjects = {
                'accepted': f"Order Accepted! - #{order.reference_id}",
                'in_progress': f"Order In Progress! - #{order.reference_id}",
                'completed': f"Order Completed! - #{order.reference_id}",
                'declined': f"Order Update - #{order.reference_id}",
            }
            
            subject = status_subjects.get(order.status, f"Order Update - #{order.reference_id}")
            
            
            html_message = None
            try:
                html_message = render_to_string('emails/customer_order_status.html', {
                    'order': order
                })
            except Exception as template_error:
                print(f"Template error: {template_error}")
                
                pass
            
            if html_message:
                
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[order.email],
                )
                email.content_subtype = "html"
            else:
                
                status_messages = {
                    'accepted': "has been accepted! Waiting for payment to begin. ",
                    'in_progress': "is now in progress! Work on your rug has begun.",
                    'completed': "is completed! Your custom rug is ready.",
                    'declined': "could not be accepted at this time.",
                }
                
                plain_message = f"""
Order Status Update

Order Reference: #{order.reference_id}

Hi {order.customer_name},

Your custom rug order {status_messages.get(order.status, 'has been updated.')}

{('Update: ' + order.admin_notes) if order.admin_notes else ''}

Current Status: {order.status.title()}

If you have any questions, please reply to this email.

Thank you,
The Rugly Barnacle Team
                """
                email = EmailMessage(
                    subject=subject,
                    body=plain_message.strip(),
                    from_email="Rugly Barnacle <orders@ruglybarnacle.com>",
                    to=[order.email],
                )
            
            email.send(fail_silently=False)
            print(f"Status update email sent for order #{order.reference_id} (Status changed from {old_status} to {order.status})")
            
        except Exception as e:
            print(f"Failed to send status update email: {str(e)}")