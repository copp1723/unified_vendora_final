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
from typing import Dict, List, Optional
import base64

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

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
            return True
            
        try:
            # Create the signature string
            signature_string = f"{timestamp}{token}"
            
            # Calculate expected signature
            expected_signature = hmac.new(
                key=self.mailgun_private_key.encode(),
                msg=signature_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def extract_dealer_id(self, email_data: Dict) -> str:
        """Extract dealer ID from email headers or sender."""
        # Try to get dealer ID from custom header first
        dealer_id = email_data.get('X-Dealer-ID')
        
        if not dealer_id:
            # Extract from sender email domain or use a default
            sender = email_data.get('sender', '')
            if '@' in sender:
                domain = sender.split('@')[1]
                # Use domain as dealer ID (simplified approach)
                dealer_id = domain.replace('.', '_')
            else:
                dealer_id = 'default_dealer'
        
        return dealer_id
    
    def extract_csv_attachments(self, email_data: Dict) -> List[Dict]:
        """Extract CSV attachments from email data."""
        attachments = []
        
        # Check for attachments in the email data
        attachment_count = int(email_data.get('attachment-count', 0))
        
        for i in range(1, attachment_count + 1):
            attachment_key = f'attachment-{i}'
            content_type_key = f'content-type-{i}'
            
            if attachment_key in email_data:
                content_type = email_data.get(content_type_key, '')
                
                # Check if it's a CSV file
                if 'csv' in content_type.lower() or email_data.get(attachment_key, '').endswith('.csv'):
                    attachments.append({
                        'filename': email_data.get(attachment_key, f'attachment_{i}.csv'),
                        'content': email_data.get(f'attachment-{i}', ''),
                        'content_type': content_type
                    })
        
        return attachments
    
    def store_csv_file(self, dealer_id: str, filename: str, content: str) -> str:
        """Store CSV file in the data storage with proper naming convention."""
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean filename
        clean_filename = filename.replace(' ', '_').replace('..', '_')
        if not clean_filename.endswith('.csv'):
            clean_filename += '.csv'
        
        # Create storage path following the pattern: /incoming/{dealer_id}/{YYYYMMDD}-{filename}.csv
        storage_filename = f"{timestamp}-{clean_filename}"
        dealer_dir = os.path.join(self.data_storage_path, 'incoming', dealer_id)
        os.makedirs(dealer_dir, exist_ok=True)
        
        file_path = os.path.join(dealer_dir, storage_filename)
        
        try:
            # Decode base64 content if needed
            if content:
                try:
                    # Try to decode as base64 first
                    decoded_content = base64.b64decode(content).decode('utf-8')
                except:
                    # If that fails, treat as plain text
                    decoded_content = content
                
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(decoded_content)
                
                logger.info(f"Stored CSV file: {file_path}")
                return file_path
            else:
                logger.warning(f"No content found for attachment: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error storing CSV file {filename}: {e}")
            return None
    
    def process_webhook(self, request_data: Dict) -> Dict:
        """Process incoming Mailgun webhook request."""
        try:
            # Verify signature if available
            signature_data = request_data.get('signature', {})
            if signature_data:
                token = signature_data.get('token', '')
                timestamp = signature_data.get('timestamp', '')
                signature = signature_data.get('signature', '')
                
                if not self.verify_signature(token, timestamp, signature):
                    return {'error': 'Invalid signature', 'status': 'failed'}
            
            # Extract dealer ID
            dealer_id = self.extract_dealer_id(request_data)
            logger.info(f"Processing email for dealer: {dealer_id}")
            
            # Extract CSV attachments
            attachments = self.extract_csv_attachments(request_data)
            
            if not attachments:
                logger.info("No CSV attachments found in email")
                return {'message': 'No CSV attachments found', 'status': 'success'}
            
            # Store each CSV file
            stored_files = []
            for attachment in attachments:
                file_path = self.store_csv_file(
                    dealer_id, 
                    attachment['filename'], 
                    attachment['content']
                )
                if file_path:
                    stored_files.append(file_path)
            
            # Log the processing result
            logger.info(f"Processed {len(stored_files)} CSV files for dealer {dealer_id}")
            
            # TODO: Trigger data analysis pipeline here
            # This will be implemented in the next phase
            
            return {
                'message': f'Successfully processed {len(stored_files)} CSV files',
                'dealer_id': dealer_id,
                'files_processed': len(stored_files),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {'error': str(e), 'status': 'failed'}


def create_app(config: Dict) -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Initialize webhook handler
    webhook_handler = MailgunWebhookHandler(config)
    
    @app.route('/webhook/mailgun', methods=['POST'])
    def mailgun_webhook():
        """Handle Mailgun webhook requests."""
        try:
            # Get request data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Process the webhook
            result = webhook_handler.process_webhook(data)
            
            # Return response
            if result.get('status') == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"Error in webhook endpoint: {e}")
            return jsonify({'error': str(e), 'status': 'failed'}), 500
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({'status': 'healthy', 'service': 'vendora-mailgun-handler'}), 200
    
    return app


if __name__ == '__main__':
    # Load configuration from environment
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'MAILGUN_PRIVATE_API_KEY': os.getenv('MAILGUN_PRIVATE_API_KEY'),
        'DATA_STORAGE_PATH': os.getenv('DATA_STORAGE_PATH', '/tmp/vendora_data')
    }
    
    # Create and run the app
    app = create_app(config)
    app.run(host='0.0.0.0', port=5000, debug=True)

