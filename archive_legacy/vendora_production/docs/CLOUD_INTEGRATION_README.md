# VENDORA Cloud Platform - GCP Integration Guide

## 🚀 Overview

The VENDORA Cloud Platform integrates with Google Cloud Platform to provide real automotive business intelligence using BigQuery data, secure API key management via Secret Manager, and Firebase authentication.

## 🏗️ Architecture

```
VENDORA Cloud Platform
├── FastAPI Application (working_fastapi_cloud.py)
├── Enhanced Flow Manager (enhanced_flow_manager.py)
├── Cloud Configuration (cloud_config.py)
├── BigQuery Integration
├── Secret Manager Integration
└── Firebase Authentication
```

## 📋 Prerequisites

### GCP Setup (Already Configured)
- ✅ GCP Project: `vendora-464403`
- ✅ Service Account: `vendora@vendora-464403.iam.gserviceaccount.com`
- ✅ BigQuery API enabled
- ✅ Secret Manager API enabled
- ✅ Firebase Auth configured
- ✅ API keys stored in Secret Manager

### Required Secrets in GCP Secret Manager
- `gemini-api-key`: Google Gemini AI API key
- `mailgun-api-key`: Mailgun email service key
- `openrouter-api-key`: OpenRouter AI service key
- `supermemory-api-key`: SuperMemory service key

## 🛠️ Installation

### 1. Install Dependencies
```bash
cd working_vendora
pip install -r requirements_cloud.txt
```

### 2. Set Up GCP Authentication
```bash
# Set environment variable for service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Or authenticate using gcloud
gcloud auth application-default login
```

### 3. Verify GCP Project
```bash
# Set your GCP project
gcloud config set project vendora-464403
```

## 🚀 Quick Start

### 1. Test Cloud Connectivity
```bash
# Quick connectivity test
python test_cloud_integration.py quick

# Comprehensive test suite
python test_cloud_integration.py
```

### 2. Start the Cloud Platform
```bash
# Start with cloud integration
python working_fastapi_cloud.py

# Server will start on http://localhost:8000
```

### 3. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Test BigQuery connection
curl http://localhost:8000/cloud/bigquery/test

# Sample business query
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are our top selling vehicles this month?",
    "dealership_id": "DEMO_DEALERSHIP_001",
    "use_cloud_data": true
  }'
```

## 📊 Key Features

### Real BigQuery Integration
- Connects to actual automotive data tables
- Sales data, inventory data, customer leads
- Real-time business intelligence

### Secure Configuration
- API keys stored in GCP Secret Manager
- No hardcoded credentials
- Automatic secret refresh

### Enhanced Analytics
- AI-powered insights using real data
- Fallback to sample data if BigQuery unavailable
- Performance metrics and monitoring

## 🔧 API Endpoints

### Core Analytics
- `POST /analyze` - Process business intelligence queries
- `POST /task-status` - Get task processing status
- `GET /metrics` - System performance metrics

### Cloud Services
- `GET /cloud/config` - Cloud configuration status
- `GET /cloud/bigquery/test` - Test BigQuery connectivity

### Authentication
- `POST /auth/verify` - Verify Firebase tokens

### Demo & Testing
- `GET /demo/sample-query` - Sample automotive queries
- `GET /demo/quick-test` - Quick system test

## 📈 BigQuery Schema

The platform expects these BigQuery tables in your `automotive` dataset:

### Sales Transactions
```sql
`vendora-464403.automotive.sales_transactions`
- dealership_id: STRING
- sale_date: DATE
- vehicle_make: STRING
- vehicle_model: STRING
- sale_price: NUMERIC
```

### Inventory
```sql
`vendora-464403.automotive.inventory`
- dealership_id: STRING
- vehicle_make: STRING
- vehicle_model: STRING
- model_year: INT64
- list_price: NUMERIC
- status: STRING
```

### Customer Leads
```sql
`vendora-464403.automotive.customer_leads`
- dealership_id: STRING
- first_contact_date: DATE
- lead_source: STRING
- status: STRING
```

## 🔍 Sample Queries

### Business Intelligence Queries
```json
{
  "query": "What were our best selling vehicles last month?",
  "dealership_id": "DEALERSHIP_001",
  "use_cloud_data": true
}
```

```json
{
  "query": "How is our inventory performing compared to last quarter?",
  "dealership_id": "DEALERSHIP_001", 
  "use_cloud_data": true
}
```

```json
{
  "query": "Show me customer conversion rates by lead source",
  "dealership_id": "DEALERSHIP_001",
  "use_cloud_data": true
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Override GCP project
export GOOGLE_CLOUD_PROJECT=vendora-464403

# Service account credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Cloud Configuration
The `cloud_config.py` module automatically:
- Initializes BigQuery client
- Loads secrets from Secret Manager
- Configures Gemini AI with API keys
- Provides fallback mechanisms

## 🧪 Testing

### Quick Test
```bash
python test_cloud_integration.py quick
```

### Comprehensive Test Suite
```bash
python test_cloud_integration.py
```

### Test Coverage
- ✅ Cloud configuration initialization
- ✅ BigQuery connectivity
- ✅ Secret Manager access
- ✅ Enhanced flow manager
- ✅ FastAPI endpoints
- ✅ Error handling and fallbacks

## 📊 Monitoring

### System Metrics
Access `/metrics` endpoint for:
- Query processing statistics
- BigQuery usage metrics
- Success/failure rates
- GCP integration status

### Health Checks
Access `/health` endpoint for:
- Service availability status
- Cloud service connections
- Configuration validation

## 🚨 Troubleshooting

### Common Issues

#### 1. BigQuery Permission Errors
```bash
# Verify service account permissions
gcloud projects get-iam-policy vendora-464403

# Ensure these roles are assigned:
# - BigQuery Data Viewer
# - BigQuery Job User
```

#### 2. Secret Manager Access Issues
```bash
# Test secret access
gcloud secrets versions access latest --secret="gemini-api-key"
```

#### 3. Authentication Problems
```bash
# Re-authenticate
gcloud auth application-default login

# Verify current account
gcloud auth list
```

#### 4. Import Errors
```bash
# Install missing dependencies
pip install -r requirements_cloud.txt

# Verify Google Cloud libraries
python -c "from google.cloud import bigquery; print('BigQuery OK')"
```

### Fallback Behavior
- If BigQuery is unavailable, system uses sample data
- If Secret Manager fails, system uses environment variables
- If Gemini API fails, system provides basic responses

## 🔐 Security

### Best Practices
- ✅ No API keys in code
- ✅ Service account with minimal permissions
- ✅ Secrets stored in GCP Secret Manager
- ✅ Authentication via Firebase
- ✅ CORS properly configured

### Production Considerations
- Use Firebase Admin SDK for token verification
- Implement rate limiting
- Add request logging and monitoring
- Configure appropriate CORS origins
- Use HTTPS in production

## 📝 Development

### Adding New BigQuery Tables
1. Create table in `vendora-464403.automotive` dataset
2. Add query logic to `enhanced_flow_manager.py`
3. Update `_determine_required_tables()` method
4. Test with sample queries

### Adding New Secrets
1. Store secret in GCP Secret Manager
2. Add to `cloud_config.py` initialization
3. Use via `self.config["secret_name"]`

## 🎯 Next Steps

### Recommended Enhancements
1. **Real Data Integration**: Populate BigQuery with actual dealership data
2. **Advanced Analytics**: Machine learning models for predictions
3. **Dashboard UI**: React/Vue frontend for visual analytics
4. **Mobile App**: Native mobile application
5. **Third-party Integrations**: CRM, DMS, marketing platforms

### Deployment Options
1. **Google Cloud Run**: Serverless container deployment
2. **Google Kubernetes Engine**: Scalable container orchestration
3. **Compute Engine**: VM-based deployment
4. **Firebase Hosting**: Static frontend hosting

## 📞 Support

For issues with the cloud integration:
1. Check the logs in the FastAPI application
2. Run the test suite for diagnostics
3. Verify GCP permissions and configuration
4. Review the troubleshooting section above

---

**VENDORA Cloud Platform v2.0** - Powered by Google Cloud Platform