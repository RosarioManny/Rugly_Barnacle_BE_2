import os
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import datetime
from ..models import NewsletterSubscriber   

host_email = os.getenv('EMAIL_HOST_USER')

class NewsletterEmailService:

    # NEWSLETTER SIGNUP
    @staticmethod
    def send_newsletter_signup_confirmation(email):
        try:
            context = {
                'subscriber_name': email,
                'unsubscribe_url': f"{os.getenv('SITE_URL')}/newsletter/unsubscribe/",
                'site_url': os.getenv('SITE_URL')
            }

            html_content = render_to_string('/newletters/newsletter_sign_up.html', context)

            email_message = EmailMessage(
                subject='Welcome to The Rugly Barnacle Newsletter!',
                body=html_content,
                from_email=host_email,
                to=[email],
            )

            email_message.content_subtype = 'html'
            email_message.send()
        except Exception as e:
            print(f"Failed to send newsletter confirmation to {email}: {e}")
            raise

        """ Send confirmation email to new newsletter subscriber """
    # DELETE EMAIL FROM DB IF UNSUBSCRIBED
    @staticmethod
    def delete_user_from_newsletter(email: str):
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
        


@staticmethod
def send_newsletter_updates(trigger_instance):
    from ..models import NewsletterSubscriber, BlogPost, Event

    # ---- Cooldown Check ----
    COOLDOWN_KEY = 'newsletter_last_sent'
    COOLDOWN_HOURS = 24  # ONCE EVERY 24 HOURS

    if cache.get(COOLDOWN_KEY):
        print(f"Newsletter cooldown active — skipping send triggered by {trigger_instance}")
        return

    try:
        subscribers = NewsletterSubscriber.objects.filter(status='subscribed')

        if not subscribers.exists():
            print("No active subscribers to send to.")
            return

        blog_posts = BlogPost.objects.order_by('-created_at')[:1]
        events = Event.objects.filter(status='upcoming').order_by('start_time')[:3]

        context = {
            'newsletter_date': datetime.now(),
            'blog_posts': [
                {
                    'title': post.title,
                    'content': post.content,
                    'created_at': post.created_at,
                    'slug': None,
                }
                for post in blog_posts
            ],
            'events': [
                {
                    'title': event.title,
                    'event_date': event.start_time,
                    'event_time': event.start_time.strftime('%I:%M %p'),
                    'location': event.location,
                    'description': event.description,
                    'ticket_link': event.ticket_link,
                }
                for event in events
            ],
            'products': [],
            'site_url': os.getenv('SITE_URL'),
        }

        for subscriber in subscribers:
            context['unsubscribe_url'] = f"{os.getenv('SITE_URL')}/newsletter/unsubscribe/?email={subscriber.email}"

            html_content = render_to_string('emails/newsletter_update.html', context)

            email_message = EmailMessage(
                subject=f"The Rugly Barnacle Newsletter - {datetime.now().strftime('%B %Y')}",
                body=html_content,
                from_email=host_email,
                to=[subscriber.email],
            )
            email_message.content_subtype = 'html'
            email_message.send()
            print(f"Newsletter sent to {subscriber.email}")

        # ---- Set cooldown AFTER successful send ----
        cache.set(COOLDOWN_KEY, True, timeout=60 * 60 * COOLDOWN_HOURS)
        print(f"Cooldown set for {COOLDOWN_HOURS} hours.")

    except Exception as e:
        print(f"Failed to send newsletter updates: {e}")
        raise