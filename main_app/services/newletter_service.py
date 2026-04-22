import os
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import datetime


host_email = os.getenv('EMAIL_HOST_USER')

class NewsletterEmailService:

    # NEWSLETTER SIGNUP
    @staticmethod
    def send_newsletter_signup_confirmation(email):
        try:
            context = {
                'subscriber_name': email,
                'unsubscribe_url': f"{os.getenv('SITE_URL')}/newsletter/unsubscribe/",
                'site_url': os.getenv('SITE_URL'),
                'logo_url': os.getenv('CLOUDINARY_LOGO_URL'), 
            }

            html_content = render_to_string('newsletters/newsletter_sign_up.html', context)

            email_message = EmailMessage(
                subject='Welcome to The Rugly Barnacle Newsletter!',
                body=html_content,
                from_email=f"The Rugly Barnacle <{host_email}>",
                to=[email],
            )
            email_message.content_subtype = 'html'
            email_message.send()
        except Exception as e:
            print(f"Failed to send newsletter confirmation to {email}: {e}")
            raise

    # DELETE EMAIL FROM DB IF UNSUBSCRIBED
    @staticmethod
    def delete_user_from_newsletter(email: str):
        from ..models import NewsletterSubscriber
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            subscriber.delete()
            print(f"Subscriber {email} deleted successfully.")
        except NewsletterSubscriber.DoesNotExist:
            print(f"Subscriber {email} not found in the database.")
            raise
        except Exception as e:
            print(f"Failed to delete subscriber {email}: {e}")
            raise

    # SEND NEWSLETTER POST TO ALL SUBSCRIBERS
    @staticmethod
    def send_newsletter_updates(post):
        from ..models import NewsletterSubscriber

        # ---- Cooldown Check ----
        COOLDOWN_KEY = f'newsletter_last_sent_{post.pk}'
        COOLDOWN_HOURS = 24

        if cache.get(COOLDOWN_KEY):
            print(f"Newsletter cooldown active — skipping send for post: {post.title}")
            return

        try:
            subscribers = NewsletterSubscriber.objects.filter(status='subscribed')

            if not subscribers.exists():
                print("No active subscribers to send to.")
                return

            images = post.images.all().order_by('order')

            if not images.exists():
                print(f"Post '{post.title}' has no images — aborting send.")
                return

            for subscriber in subscribers:
                context = {
                    'post': post,
                    'images': images,
                    'newsletter_date': datetime.now(),
                    'site_url': os.getenv('SITE_URL'),
                    'logo_url': os.getenv('CLOUDINARY_LOGO_URL'),
                    'unsubscribe_url': f"{os.getenv('SITE_URL')}/newsletter/unsubscribe/?email={subscriber.email}",
                }

                html_content = render_to_string('newsletters/newsletter_post.html', context)

                email_message = EmailMessage(
                    subject=f"The Rugly Barnacle Newsletter - {datetime.now().strftime('%B %Y')}",
                    body=html_content,
                    from_email=f"The Rugly Barnacle <{host_email}>",
                    to=[subscriber.email],
                )
                email_message.content_subtype = 'html'
                email_message.send()
                print(f"Newsletter sent to {subscriber.email}")

            # ---- Set cooldown AFTER successful send ----
            cache.set(COOLDOWN_KEY, True, timeout=60 * 60 * COOLDOWN_HOURS)
            print(f"Cooldown set for {COOLDOWN_HOURS} hours. Post: {post.title}")

        except Exception as e:
            print(f"Failed to send newsletter updates: {e}")
            raise