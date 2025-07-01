"""Email processor module for VENDORA platform."""

from .mailgun_handler import MailgunWebhookHandler, create_app

__all__ = ['MailgunWebhookHandler', 'create_app']

