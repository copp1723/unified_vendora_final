# VENDORA Hierarchical Flow Implementation

## Overview

The VENDORA platform now implements a complete **3-Level Hierarchical Agent Architecture** that ensures every analytical insight passes through multiple validation layers before reaching users. This architecture prioritizes **quality, reliability, and trustworthiness**.

## Architecture

### Level 1: The Orchestrator (Front Desk)
- **File**: `services/vendora_orchestrator.py`
- **Role**: Task ingestion and intelligent dispatch
- **Responsibilities**:
  - Receives user queries
  - Analyzes complexity and requirements
  - Routes to appropriate L2 specialist
  - Formats final responses for users

### Level 2: Specialist Agents (Workshop)
- **File**: `services/vendora_specialists.py`
- **Agents**:
  - **Data Analyst Agent**: Standard queries, KPIs, trends
  - **Senior Analyst Agent**: Complex forecasting, predictive analytics
- **Responsibilities**:
  - Generate SQL queries
  - Analyze data
  - Create draft insights
  - Respond to revision requests

### Level 3: Master Analyst (Editor-in-Chief)
- **File**: `services/vendora_master_analyst.py`
- **Role**: Quality gate and validation authority
- **Responsibilities**:
  - Validate data accuracy
  - Check methodology rigor
  - Verify business logic
  - Ensure compliance
  - Approve or reject insights

## Flow Sequence

```
User Query → L1 Orchestrator → L2 Specialist → L3 Master Analyst → L1 Orchestrator → User
                                      ↑                    ↓
                                      ←── Revision Loop ───┘
```

## Key Components

### Hierarchical Flow Manager
- **File**: `services/hierarchical_flow_manager.py`
- Coordinates the entire flow
- Manages state and task tracking
- Handles revision loops
- Provides metrics and monitoring

### Integration Points

1. **API Endpoints** (`src/enhanced_main.py`):
   - `POST /api/v1/query` - Process user queries
   - `GET /api/v1/task/<id>/status` - Check task status
   - `GET /api/v1/system/metrics` - System metrics

2. **Explainability Engine**:
   - Tracks all agent operations
   - Provides transparency
   - Enables debugging and monitoring

## Usage Example

```python
# Process a user query
curl -X POST http://localhost:5001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were my top selling vehicles last month?",
    "dealership_id": "dealer_123",
    "context": {
      "user_role": "sales_manager"
    }
  }'
```

## Quality Assurance Features

1. **Multi-Stage Validation**:
   - Data accuracy verification
   - Methodology validation
   - Business logic checks
   - Compliance verification

2. **Revision System**:
   - Master Analyst can request revisions
   - Up to 2 revision attempts
   - Specific feedback provided

3. **Confidence Scoring**:
   - Each insight has a confidence score
   - Quality threshold: 85% (configurable)
   - Different thresholds for different complexity levels

## Configuration

Required environment variables:
```bash
GEMINI_API_KEY=your-gemini-api-key
BIGQUERY_PROJECT=your-bigquery-project
MAILGUN_PRIVATE_API_KEY=your-mailgun-key
```

## Testing

Run the test suite:
```bash
python test_hierarchical_flow.py
```

This tests:
- Simple, standard, complex, and critical queries
- Revision flows
- Error handling
- System metrics

## Benefits

1. **Reliability**: No unvalidated insights reach users
2. **Quality**: Multiple validation layers ensure accuracy
3. **Transparency**: Full audit trail of decisions
4. **Scalability**: Modular architecture allows easy expansion
5. **Intelligence**: Adaptive complexity routing

## Next Steps

1. Configure Google Cloud credentials
2. Set up BigQuery tables
3. Configure Gemini API access
4. Deploy to Google Cloud Run
5. Connect frontend UI

The hierarchical flow system is now the core of VENDORA, ensuring that every piece of analytical insight meets the highest standards of quality and reliability.
