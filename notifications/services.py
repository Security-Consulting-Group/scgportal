from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse

def send_email_notification(request, subject, template_name, context, recipient_list):
    current_site = get_current_site(request)
    context['site_name'] = current_site.name

    message = render_to_string(template_name, context)
    html_message = render_to_string(template_name, context)
    from_email = settings.DEFAULT_FROM_EMAIL

    if settings.DEBUG:
        print(f"Subject: {subject}")
        print(f"From: {from_email}")
        print(f"To: {', '.join(recipient_list)}")
        print(f"Message:\n{message}")
    else:
        send_mail(subject, message, from_email, recipient_list, html_message=html_message)

def send_password_reset_email(request, user, reset_url):
    subject = f"[SCG] - Password Reset Request"
    template_name = 'notifications/password_reset_email.html'
    context = {
        'user': user,
        'reset_url': reset_url,
    }
    send_email_notification(request, subject, template_name, context, [user.email])

def send_new_user_notification(request, new_user):
    subject = f"[SCG] - Welcome to SCG Portal"
    template_name = 'notifications/new_user_email.html'
    
    # Generate password reset token
    token = default_token_generator.make_token(new_user)
    uid = urlsafe_base64_encode(force_bytes(new_user.pk))
    
    # Construct reset URL
    reset_url = request.build_absolute_uri(
        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    context = {
        'user': new_user,
        'reset_url': reset_url,
    }
    send_email_notification(request, subject, template_name, context, [new_user.email])

# Add more notification functions as needed