# cloud_function_email_handler/main.py

import functions_framework
import hmac
import os
import hashlib
import logging
from google.cloud import vision

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def handle_email_webhook(request):
    """
    Cloud Function to handle incoming emails from Mailgun.
    Triggered by a Mailgun webhook (HTTP POST).
    """
    logger.info("Received Mailgun webhook request.")

    # Access form data sent by Mailgun (typically multipart/form-data)
    request_form = request.form

    # Print the form data for inspection during initial development
    logger.info(f"Received form data: {request_form}")

    # Extract core email data
    sender = request_form.get('sender')
    recipient = request_form.get('recipient')
    subject = request_form.get('subject')
    body_plain = request_form.get('body-plain')

    logger.info(f"Extracted Data: Sender={sender}, Recipient={recipient}, Subject={subject[:50]}...") # Log truncated subject
    logger.debug(f"Body Plain: {body_plain[:200]}...") # Log truncated body plain

    # --- Mailgun Signature Verification (Step 1.2) ---
    signature = request_form.get('signature')
    timestamp = request_form.get('timestamp')
    token = request_form.get('token')

    # Get your Mailgun webhook signing key from environment variables
    # IMPORTANT: In production, use Google Cloud Secrets Manager to store keys securely
    mailgun_signing_key = os.getenv('MAILGUN_WEBHOOK_SIGNING_KEY')

    if not mailgun_signing_key:
        logger.error("MAILGUN_WEBHOOK_SIGNING_KEY environment variable not set.")
        return 'Configuration Error: Mailgun signing key missing.', 500 # Or a different error code if preferred

    # Calculate the expected signature
    hmac_code = hmac.new(key=mailgun_signing_key.encode(),
                          msg=f'{timestamp}{token}'.encode(),
                          digestmod=hashlib.sha256).hexdigest()

    if not hmac.compare_digest(str(hmac_code), str(signature)):
        logger.error(f"Mailgun signature verification failed. Received: {signature}, Expected: {hmac_code}")
        return 'Invalid signature', 401
    logger.info("Mailgun signature verified successfully.")

    # --- Attachment Processing (Step 1.3) ---
    attachments = request.files.getlist('attachment') # 'attachment' is the default name used by Mailgun
    logger.info(f"Found {len(attachments)} attachment(s).")

    extracted_attachment_data = [] # List to store data extracted from attachments

    for attachment in attachments:
        logger.info(f"Processing attachment: {attachment.filename}, Content-Type: {attachment.content_type}")
        if attachment.content_type in ['image/jpeg', 'image/png', 'application/pdf', 'image/gif', 'image/tiff']: # Include more image types
            logger.info(f"Attachment {attachment.filename} is an image or PDF. Placeholder for Vision API call.")
            try:
                # Initialize Vision API client inside the loop for simplicity in this example,
                # but consider initializing outside for performance in production.
                client = vision.ImageAnnotatorClient()

                content = attachment.read()
                image = vision.Image(content=content)

                # Use document_text_detection for better results on scanned documents
                response = client.document_text_detection(image=image)
                extracted_text = response.full_text_annotation.text if response.full_text_annotation else ""
                extracted_attachment_data.append({"filename": attachment.filename, "text": extracted_text})
                logger.info(f"Successfully extracted text from {attachment.filename} (first 100 chars): {extracted_text[:100]}...")
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.filename} with Vision API: {str(e)}", exc_info=True)
                # Decide how to handle errors: skip attachment, raise error, etc.

        else:
            logger.info(f"Attachment {attachment.filename} is of type {attachment.content_type}, skipping Vision API processing.")

    # TODO: Implement data normalization (Step 1.4)
    # TODO: Implement data loading to BigQuery (Step 1.5)
    # TODO: Implement comprehensive error handling and logging (Step 1.6)

    # For now, just acknowledge receipt