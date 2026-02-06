from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

def send_contact_email(subject, message, email, name="Anonymous"):
    # Send TO the admin (FitMitra) FROM the system
    # The user's email is in the message body
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    full_message = f"""
You have received a new message from the FitMitra Contact Form:

--------------------------------------------------
Sender Name: {name}
Sender Email: {email}
Timestamp: {timestamp}
--------------------------------------------------

Message:
{message}

--------------------------------------------------
Reply directly to this email to contact the user.
"""
    
    send_mail(
        f"New Contact Message: {subject}", # Prefix subject for clarity
        full_message,
        settings.DEFAULT_FROM_EMAIL, # From system (authenticated)
        [settings.EMAIL_HOST_USER], # To Admin (You)
        fail_silently=False
    )
