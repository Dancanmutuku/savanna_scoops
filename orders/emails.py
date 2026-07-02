import logging
import threading

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Order

logger = logging.getLogger(__name__)


def _send_via_brevo(subject, body, recipient_email):
    response = requests.post(
        settings.BREVO_API_URL,
        headers={
            'accept': 'application/json',
            'api-key': settings.BREVO_API_KEY,
            'content-type': 'application/json',
        },
        json={
            'sender': {
                'name': settings.DEFAULT_FROM_NAME,
                'email': settings.DEFAULT_FROM_EMAIL,
            },
            'to': [{'email': recipient_email}],
            'subject': subject,
            'htmlContent': body,
        },
        timeout=15,
    )
    response.raise_for_status()


def _send_via_resend(subject, body, recipient_email):
    response = requests.post(
        settings.RESEND_API_URL,
        headers={
            'Authorization': f'Bearer {settings.RESEND_API_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'from': f'{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
            'to': [recipient_email],
            'subject': subject,
            'html': body,
        },
        timeout=15,
    )
    response.raise_for_status()


def send_order_confirmation_email(order_id):
    try:
        order = Order.objects.prefetch_related('items').get(id=order_id)
    except Order.DoesNotExist:
        logger.warning("Skipping order confirmation email; order %s no longer exists.", order_id)
        return

    if not order.customer_email:
        logger.info("Skipping order confirmation email for %s; no customer email.", order.order_number)
        return

    subject = f"Order Confirmed - {order.order_number} | Savanna Scoops"
    body = render_to_string('emails/order_confirmation.html', {'order': order})
    try:
        if settings.EMAIL_DELIVERY_BACKEND == 'resend' and settings.RESEND_API_KEY:
            _send_via_resend(subject, body, order.customer_email)
        elif settings.EMAIL_DELIVERY_BACKEND == 'brevo' and settings.BREVO_API_KEY:
            _send_via_brevo(subject, body, order.customer_email)
        else:
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [order.customer_email],
                html_message=body,
                fail_silently=False,
            )
    except Exception:
        logger.exception("Failed to send confirmation email for %s.", order.order_number)


def queue_order_confirmation_email(order_id):
    if settings.EMAIL_SEND_ASYNC:
        thread = threading.Thread(
            target=send_order_confirmation_email,
            args=(order_id,),
            daemon=True,
            name=f'order-email-{order_id}',
        )
        thread.start()
        return

    send_order_confirmation_email(order_id)
