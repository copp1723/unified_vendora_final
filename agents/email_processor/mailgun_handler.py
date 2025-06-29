"""
Mailgun webhook handler for VENDORA automotive data platform.
Receives emails with CSV attachments and triggers data processing pipeline.
"""

import os
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MailgunWebhookHandler:
    """Handles Mailgun webhook requests and processes automotive data."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.mailgun_private_key = config.get('MAILGUN_PRIVATE_API_KEY')
        self.data_storage_path = config.get('DATA_STORAGE_PATH', '/tmp/vendora_data')
        
        # Ensure data storage directory exists
        os.makedirs(self.data_storage_path, exist_ok=True)
        os.makedirs(f"{self.data_storage_path}/incoming", exist_ok=True)
        os.makedirs(f"{self.data_storage_path}/processed", exist_ok=True)
    
    def verify_signature(self, token: str, timestamp: str, signature: str) -> bool:
        """Verify Mailgun webhook signature for security."""
        if not self.mailgun_private_key:
            logger.warning("No Mailgun private key configured - skipping signature verification")
            # In a production environment, you might want to make this False if the key is missing
            # For now, allowing it to pass if no key is set, to simplify local dev if key is not set up.
            return True
            
        try:
            signature_string = f"{timestamp}{token}"
            expected_signature = hmac.new(
                key=self.mailgun_private_key.encode(),
                msg=signature_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def extract_dealer_id(self, email_data: Dict[str, Any]) -> str:
        """Extract dealer ID from email headers or sender."""
        # Mailgun often sends custom headers as 'message-headers'
        message_headers_raw = email_data.get('message-headers')
        dealer_id = None

        if message_headers_raw:
            try:
                message_headers = json.loads(message_headers_raw) if isinstance(message_headers_raw, str) else message_headers_raw
                # Headers are often a list of [name, value] pairs
                for header_pair in message_headers:
                    if isinstance(header_pair, list) and len(header_pair) == 2 and header_pair[0].lower() == 'x-dealer-id':
                        dealer_id = header_pair[1]
                        break
            except json.JSONDecodeError:
                logger.warning("Could not parse message-headers as JSON.")
            except Exception as e:
                logger.warning(f"Error processing message-headers: {e}")


        if not dealer_id:
            dealer_id = email_data.get('X-Dealer-ID') # Check top-level if not in message-headers

        if not dealer_id:
            sender = email_data.get('sender', '') or email_data.get('From', '')
            if '@' in sender:
                domain = sender.split('@')[1]
                dealer_id = domain.replace('.', '_').split('>')[0].strip() # Clean up potential trailing chars
            else:
                dealer_id = 'default_dealer'
        
        return dealer_id
    
    def extract_csv_attachments(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract CSV attachments from email data."""
        attachments = []
        
        # Mailgun provides attachments in a list under 'attachments'
        # or as 'attachment-x' for form data. We should primarily rely on 'attachments' if available (JSON).
        
        if 'attachments' in email_data and isinstance(email_data['attachments'], list):
            for attachment_data in email_data['attachments']:
                content_type = attachment_data.get('content-type', '')
                filename = attachment_data.get('name', 'unknown.csv') # Mailgun uses 'name' for filename
                
                if 'csv' in content_type.lower() or filename.lower().endswith('.csv'):
                    # Content is usually base64 encoded by Mailgun when sent as JSON
                    # However, the 'content' field might not exist if it's a large file and 'url' is used.
                    # For this implementation, we assume content is directly available or handled by Mailgun's parsing.
                    # If Mailgun sends form-data, it might be directly in 'attachment-x'.
                    # This handler expects the content to be decoded by the FastAPI layer if it's form data.
                    # For JSON payload, Mailgun might provide 'content' directly (often not for files) or a URL.
                    # This version will assume 'content' is provided as a string (potentially base64 encoded).
                    # A more robust solution would handle fetching from 'url' if 'content' is missing.

                    # Mailgun's webhook structure for attachments (when received as JSON) might have 'content'
                    # but it's often not the actual file content but metadata.
                    # The actual file content is typically accessed via form fields 'attachment-x'
                    # or downloaded via a URL provided in the 'attachments' array.
                    # For simplicity, this example will assume the content is directly available in the `email_data`
                    # passed to this function, which the FastAPI endpoint will need to prepare.
                    # Let's assume `email_data` might contain `attachment-1`, `attachment-2` etc.
                    # if parsed from form-data by FastAPI.

                    # This method needs to be more flexible based on how FastAPI presents the data.
                    # For now, let's assume the FastAPI endpoint will populate a simplified structure.
                    # The plan was to adapt `process_webhook` to accept FastAPI's `Request` object.
                    # The endpoint will extract files and pass them.
                    # So, this function will receive a list of dicts directly.
                    pass # This logic will be simplified as the FastAPI endpoint will handle file extraction.

        # Simplified: assume attachments are passed in a specific format by the calling FastAPI endpoint
        # The FastAPI endpoint will be responsible for extracting file content (e.g., from UploadFile)
        # and passing it to `process_webhook`, which then calls this.
        # Let's adjust `process_webhook` and the FastAPI endpoint to handle this.
        # For now, this function will expect `email_data` to contain a pre-processed list of attachments.

        processed_attachments = []
        raw_attachments = email_data.get('parsed_attachments', []) # Expecting this from FastAPI layer

        for att in raw_attachments:
            filename = att.get('filename', 'unknown.csv')
            content = att.get('content', '') # Expecting decoded content string
            content_type = att.get('content_type', '')

            if ('csv' in content_type.lower() or filename.lower().endswith('.csv')) and content:
                 processed_attachments.append({
                    'filename': filename,
                    'content': content, # Expecting already decoded string content
                    'content_type': content_type
                })
            elif not content:
                logger.warning(f"Attachment {filename} has no content.")

        return processed_attachments

    def store_csv_file(self, dealer_id: str, filename: str, content: str) -> Optional[str]:
        """Store CSV file in the data storage with proper naming convention.
        Content is expected to be a decoded string.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        clean_filename = "".join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in filename)
        if not clean_filename.endswith('.csv'):
            clean_filename += '.csv'
        
        storage_filename = f"{timestamp}-{clean_filename}"
        dealer_dir = os.path.join(self.data_storage_path, 'incoming', dealer_id)
        os.makedirs(dealer_dir, exist_ok=True)
        
        file_path = os.path.join(dealer_dir, storage_filename)
        
        try:
            if content:
                # Content is already a string, write directly
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Stored CSV file: {file_path}")
                return file_path
            else:
                logger.warning(f"No content found for attachment: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error storing CSV file {filename}: {e}")
            return None
    
    async def process_webhook(self, request_data: Dict[str, Any], parsed_attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process incoming Mailgun webhook request.
        request_data: The parsed JSON or form data from the webhook.
        parsed_attachments: A list of dictionaries, where each dict has 'filename', 'content' (decoded string), 'content_type'.
        """
        try:
            # Signature verification (assuming signature components are top-level in request_data)
            # Mailgun usually sends signature data in a 'signature' dictionary for JSON,
            # or as separate fields ('token', 'timestamp', 'signature') for form data.
            sig_data = request_data.get('signature', {})
            token = sig_data.get('token') or request_data.get('token')
            timestamp = sig_data.get('timestamp') or request_data.get('timestamp')
            signature = sig_data.get('signature') or request_data.get('signature') # field name from Mailgun is 'signature'
            
            if token and timestamp and signature:
                if not self.verify_signature(token, str(timestamp), signature): # timestamp needs to be string
                    logger.warning("Invalid signature for webhook request.")
                    return {'error': 'Invalid signature', 'status': 'failed'}
            else:
                # If signature parts are missing, log it. Depending on policy, might reject.
                logger.warning("Signature components missing in webhook data. Skipping verification.")


            # Extract dealer ID from the main body of the request data
            # This might contain fields like 'sender', 'To', 'From', 'subject', etc.
            # Also custom headers if Mailgun includes them (e.g. 'message-headers').
            dealer_id = self.extract_dealer_id(request_data)
            logger.info(f"Processing email for dealer: {dealer_id}")
            
            # Use pre-parsed attachments passed from the FastAPI endpoint
            # The `extract_csv_attachments` function is now simpler and expects this format.
            # This avoids MailgunWebhookHandler needing to know about FastAPI's UploadFile.
            csv_attachments = self.extract_csv_attachments({'parsed_attachments': parsed_attachments})
            
            if not csv_attachments:
                logger.info("No CSV attachments found or processed from email")
                return {'message': 'No valid CSV attachments found', 'status': 'success_no_files'}
            
            stored_files_paths = []
            for attachment in csv_attachments:
                file_path = self.store_csv_file(
                    dealer_id, 
                    attachment['filename'], 
                    attachment['content'] # content is already a decoded string
                )
                if file_path:
                    stored_files_paths.append(file_path)
            
            logger.info(f"Processed {len(stored_files_paths)} CSV files for dealer {dealer_id}")
            
            # TODO: Trigger data analysis pipeline here
            
            return {
                'message': f'Successfully processed {len(stored_files_paths)} CSV files',
                'dealer_id': dealer_id,
                'files_processed_count': len(stored_files_paths),
                'file_paths': stored_files_paths, # Good for debugging/logging
                'status': 'success'
            }
            
        except Exception as e:
            logger.exception(f"Error processing webhook: {e}") # Use logger.exception for stack trace
            return {'error': str(e), 'status': 'failed'}

# Removed Flask create_app and if __name__ == '__main__' block
# This file now only contains the MailgunWebhookHandler class.
# Pandas import was not used, so it's removed. If CSV processing beyond storage is needed later, it can be re-added.
# json import is used by extract_dealer_id for message-headers.
