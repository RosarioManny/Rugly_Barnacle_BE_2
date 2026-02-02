from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os

host_email = os.getenv('EMAIL_HOST_USER')
class NewsletterEmailService:
  
    # DELETE EMAIL FROM DB IF UNSUBSCRIBED
    # SEND NEWSLETTER WHEN EVENT OR BLOG IS PUBLISHED
    # NEWSLETTER SIGNUP
    @staticmethod
    def send_newsletter_signup_confirmation(email):
        """ Send confirmation email to new newsletter subscriber """
    