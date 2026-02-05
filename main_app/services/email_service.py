# main_app/services/email_service.py
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os

host_email = os.getenv('EMAIL_HOST_USER')

class OrderEmailService:
    
    # TO OWNER
    @staticmethod
    def send_order_notification(order):
        """Send notification to owner about new order"""
        try:
            # Validate essential data
            if not host_email:
                print("ERROR: host_email environment variable not set")
                return False
                
            if not order.email:
                print("ERROR: Customer email is missing from order")
                
            subject = f"RB New Custom Order - #{order.reference_id}"
            customer_email = order.email
            
            # Try to load HTML template with correct paths
            html_message = None
            template_paths_to_try = [
                'emails/custom_order_notification.html', 
            ]
            
            for template_path in template_paths_to_try:
                try:
                    print(f"DEBUG: Trying template path: {template_path}")
                    html_message = render_to_string(template_path, {'order': order})
                    print(f"DEBUG: Successfully loaded template: {template_path}")
                    break
                except Exception as template_error:
                    print(f"DEBUG: Failed to load {template_path}: {template_error}")
                    continue
            
            # Fallback to plain text if HTML template not found
            if html_message is None:
                print("DEBUG: Using plain text fallback - no template found")
                return OrderEmailService._send_plain_text_notification(order)
            
            # Create and send HTML email
            email = EmailMessage(
                subject=subject, # <- The title of the email
                body=html_message, # <- The content of the email
                from_email=f"The Rugly Barnacle <{host_email}>", # <- The senders name 
                to=[host_email], # <- Who it's sent too
                reply_to=[customer_email]
            )
            email.content_subtype = 'html'
            has_image = order.images.exists()
            print(f"DEBUG: Attempting to send email to: {[host_email]}")
            print(f"DEBUG: Image Provided: {has_image}")
            email.send(fail_silently=False)
            print(f"SUCCESS: Order notification email sent for order #{order.reference_id}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to send order notification: {str(e)}")
            import traceback
            print(f"ERROR TRACEBACK: {traceback.format_exc()}")
            # Try plain text as last resort
            try:
                OrderEmailService._send_plain_text_notification(order)
            except Exception as fallback_error:
                print(f"CRITICAL: All email methods failed: {fallback_error}")
            return False
        
    @staticmethod 
    def _send_plain_text_notification(order):
        """Private method for plain text fallback"""
        try:
            subject = f"RB New Custom Order - #{order.reference_id}"
            customer_email = order.email
            
            has_images = order.images.exists()
            image_info = "INCLUDES REFERENCE IMAGE(S)" if has_images else "NO REFERENCE IMAGES - Consider asking for visual references"
            
            plain_message = f"""
NEW CUSTOM ORDER RECEIVED!

ORDER DETAILS:
──────────────
Reference ID: #{order.reference_id}
Customer Name: {order.customer_name}
Customer Email: {order.email}
Preferred Contact: {order.contact_method.title()}
Contact Info: {order.contact_info or 'Use email above'}
Image Status: {image_info}

DESIGN DESCRIPTION:
──────────────────
{order.description}

ORDER STATUS:
─────────────
Status: {order.status.title()}
Submitted: {order.created_at}

ACTION REQUIRED:
• Review the order details above
{'• Check reference images in admin panel' if has_images else '• Consider asking customer for reference images'}
• Update order status in admin panel  
• Contact customer within 24-48 hours
• Provide quote and timeline
"""

            
            email = EmailMessage(
                subject=subject,
                body=plain_message.strip(),  # Changed from 'message' to 'body'
                from_email=f"The Rugly Barnacle <{host_email}>",
                to=[host_email],  # Changed from 'recipient_list' to 'to'
                reply_to=[customer_email]  # Ensure this is a list
            )
            
            email.send(fail_silently=False)
            print(f"Plain text email sent for order #{order.reference_id}")
            return True

        except Exception as e:
            print(f"Failed to send plain text email: {e}")
            return False
    
    # CUSTOMER
    @staticmethod
    def send_order_confirmation(order):
        """Send confirmation email to customer"""
        try:
            customer_email = order.email
            subject = f"Custom Order Request - #{order.reference_id}"
            
            html_message = None
            try:
                html_message = render_to_string('emails/customer_confirmation.html', { 
                    'order': order
                })
            except Exception as e:
                print(f"Template error: {e}")
                pass
            
            if html_message:  # HTML email if found
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=f"The Rugly Barnacle <{host_email}>",
                    to=[customer_email],
                )
                email.content_subtype = "html"
            else:  # Plain text fallback
                has_images = order.images.exists()
                
                if has_images:
                    image_section = f"""
IMAGE CONFIRMATION:
──────────────────
Perfect! I've received your reference image and will use it as a visual guide while creating your custom rug. 
Feel free to send any additional inspiration photos by replying to this email!
"""
                else:
                    image_section = f"""
VISUAL REFERENCES:
─────────────────
Want to make sure I capture your vision perfectly? Reference images are incredibly helpful! 
You can send photos, color swatches, or design inspiration by simply replying to this email 
with your images attached. The more visual references, the better!
"""
                
                plain_message = f"""
Thank you for your custom order with Rugly Barnacle!

ORDER CONFIRMATION:
──────────────────
Order Reference: #{order.reference_id}
Customer Name: {order.customer_name}
Submitted: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}

{image_section}

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
                    from_email=f"The Rugly Barnacle <{host_email}>",
                    to=[customer_email],
                )
            
            email.send(fail_silently=False)
            print(f"Order confirmation sent to customer for order #{order.reference_id}")
            return True
            
        except Exception as e:
            print(f"Failed to send customer confirmation: {str(e)}")
            return False
    
    # CUSTOMER
    @staticmethod
    def send_status_update(order, old_status):
        """Send status update email to customer"""
        try:
            if old_status == 'pending' and order.status == 'pending':
                return
            
            # Map status to subject lines
            status_subjects = {
                'accepted': f"Order Accepted! - #{order.reference_id}",
                'in_progress': f"Order In Progress! - #{order.reference_id}",
                'completed': f"Order Completed! - #{order.reference_id}",
                'declined': f"Order Update - #{order.reference_id}",
            }
            
            subject = status_subjects.get(order.status, f"Order Update - #{order.reference_id}")
            customer_email = order.email  
            
            html_message = None
            template_paths_to_try = [
                '/emails/customer_order_status.html', 
            ]
            
            for template_path in template_paths_to_try:
                try:
                    print(f"DEBUG: Trying template path: {template_path}")
                    html_message = render_to_string(template_path, {'order': order})
                    print(f"DEBUG: Successfully loaded template: {template_path}")
                    break
                except Exception as template_error:
                    print(f"DEBUG: Failed to load {template_path}: {template_error}")
                    continue
            
            if html_message:
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=f"The Rugly Barnacle <{host_email}>",
                    to=[customer_email],  
                )
                email.content_subtype = "html"
            else:
                status_messages = {
                    'accepted': "has been accepted! $50 deposit via Zelle/Venmo required to secure your spot. Remaining balance due after rug completion.",
                    'in_progress': "is now in progress! Your rug is being created. Balance payment will be requested when your rug is finished.",
                    'completed': "is completed! Your rug is ready. Please submit the remaining balance via Zelle/Venmo to initiate shipping.",
                    'declined': "could not be accepted at this time.",
                }
                
                has_images = order.images.exists()
                image_note = ""
                
                if has_images:
                    if order.status == 'in_progress':
                        image_note = "I'm using your reference images to guide the creation process - they're super helpful!"
                    elif order.status == 'completed':
                        image_note = "Your reference images were invaluable in creating the final design!"
                    elif order.status == 'accepted':
                        image_note = "Your reference images give me a great starting point for your design!"
                else:
                    if order.status == 'accepted':
                        image_note = "Want to send reference images? They help ensure I capture your vision perfectly! Just reply with photos."
                    elif order.status == 'in_progress':
                        image_note = "It's not too late to send reference images if you have any - they can still help guide the final details!"
                
                plain_message = f"""
Order Status Update

Order Reference: #{order.reference_id}

Hi {order.customer_name},

Your custom rug order {status_messages.get(order.status, 'has been updated.')}

{image_note}

{('Update: ' + order.admin_notes) if order.admin_notes else ''}

Current Status: {order.status.title()}

If you have any questions, please reply to this email.

Thank you,
The Rugly Barnacle Team
                """
                email = EmailMessage(
                    subject=subject,
                    body=plain_message.strip(),
                    from_email=f"The Rugly Barnacle <{host_email}>",
                    to=[customer_email],  
                )
            
            email.send(fail_silently=False)
            print(f"Status update email sent for order #{order.reference_id} (Status changed from {old_status} to {order.status})")
            return True
            
        except Exception as e:
            print(f"Failed to send status update email: {str(e)}")
            return False