# VENDORA Hierarchical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              VENDORA Platform Overview                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   USER/CLIENT   │
│  (Web/Mobile)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY (Flask)                                   │
│                         /api/v1/query endpoint                                   │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      HIERARCHICAL FLOW MANAGER                                   │
│                    Coordinates the entire L1→L2→L3→L1 flow                      │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────────┐                         ┌─────────────────────┐
│  EXPLAINABILITY     │                         │    AUDIT TRAIL      │
│     ENGINE          │                         │   & MONITORING      │
│ (Tracks all ops)    │                         │                     │
└─────────────────────┘                         └─────────────────────┘

                    HIERARCHICAL AGENT FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEVEL 1: ORCHESTRATOR (The Front Desk)
┌─────────────────────────────────────────────────────────────────┐
│                     L1: ORCHESTRATOR AGENT                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐       │
│  │ Task Intake │→ │  Complexity   │→ │ Agent Dispatch  │       │
│  │             │  │  Analysis     │  │                 │       │
│  └─────────────┘  └──────────────┘  └────────┬────────┘       │
│                                               │                 │
│  Services:                                    ▼                 │
│  • Query parsing                      ┌───────────────┐        │
│  • Intent detection                   │ Route to L2   │        │
│  • Complexity scoring                 │ Specialist    │        │
│  • Response formatting                └───────┬───────┘        │
└───────────────────────────────────────────────┼─────────────────┘
                                               │
                    ┌──────────────────────────┴──────────────────┐
                    ▼                                             ▼
LEVEL 2: SPECIALISTS (The Workshop)
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│    L2: DATA ANALYST AGENT       │     │    L2: SENIOR ANALYST AGENT     │
│                                 │     │                                 │
│  For: SIMPLE & STANDARD queries │     │  For: COMPLEX & CRITICAL       │
│                                 │     │                                 │
│  Capabilities:                  │     │  Capabilities:                  │
│  • SQL generation               │     │  • Advanced SQL                 │
│  • KPI calculation              │     │  • Predictive analytics         │
│  • Trend analysis               │     │  • Forecasting                  │
│  • Basic reporting              │     │  • Anomaly detection            │
│                                 │     │  • Strategic analysis           │
│  Output: Draft Insight          │     │  Output: Draft Insight          │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                        │
                 └───────────────┬────────────────────────┘
                                 ▼
LEVEL 3: MASTER ANALYST (The Editor-in-Chief)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           L3: MASTER ANALYST AGENT                               │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Data Accuracy│→ │ Methodology  │→ │Business Logic│→ │  Compliance  │      │
│  │ Validation   │  │ Validation   │  │ Validation   │  │ Validation   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                                  │
│                              ▼                                                   │
│                    ┌───────────────────┐                                        │
│                    │ Quality Decision  │                                        │
│                    └────────┬──────────┘                                        │
│                             │                                                    │
│        ┌────────────────────┼────────────────────┐                             │
│        ▼                    ▼                    ▼                             │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐                         │
│  │ APPROVED │        │ REVISION │        │ REJECTED │                         │
│  │          │        │  NEEDED  │        │          │                         │
│  └────┬─────┘        └────┬─────┘        └──────────┘                         │
└───────┼───────────────────┼──────────────────────────────────────────────────┘
        │                    │
        │                    └──── Feedback Loop ────┐
        │                                            │
        ▼                                            ▼
┌─────────────────────┐                    (Back to L2 Specialist)
│  BACK TO L1         │                    Max 2 revision attempts
│  for user delivery  │
└─────────────────────┘

DATA FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   BigQuery   │────▶│ Gemini API   │────▶│ Validated    │
│   Data       │     │ Analysis     │     │ Insights     │
└──────────────┘     └──────────────┘     └──────────────┘

KEY FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SEPARATION OF CONCERNS
   • Each agent has one specific role
   • No conflicts of interest
   • Clean interfaces between levels

2. QUALITY GATES
   • No insight reaches users without L3 validation
   • Automated revision process
   • Audit trail for compliance

3. INTELLIGENT ROUTING
   • Complexity-based agent selection
   • Resource optimization
   • Adaptive processing

4. TRANSPARENCY
   • Full explainability of decisions
   • Real-time monitoring
   • Comprehensive audit logs

METRICS & MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────┐
│                        SYSTEM METRICS                            │
│                                                                  │
│  • Total Queries Processed      • Average Processing Time       │
│  • Approval Rate               • Revision Rate                  │
│  • Complexity Distribution     • Agent Performance              │
│  • Error Rate                  • Quality Scores                 │
└─────────────────────────────────────────────────────────────────┘
```

## Communication Protocol

### Message Flow Between Levels

```json
// L1 → L2 Message
{
  "task_id": "TASK-abc123",
  "query": "What were my top selling vehicles last month?",
  "complexity": "standard",
  "dealership_id": "dealer_123",
  "required_data": ["sales", "inventory"],
  "context": {
    "user_role": "sales_manager",
    "time_range": "last_month"
  }
}

// L2 → L3 Message
{
  "task_id": "TASK-abc123",
  "agent_id": "data_analyst",
  "draft_insight": {
    "content": {
      "summary": "Top 5 vehicles by sales volume...",
      "key_metrics": {...},
      "insights": [...],
      "recommendations": [...]
    },
    "sql_queries": [...],
    "confidence_score": 0.85,
    "methodology": {...}
  }
}

// L3 → L1 Message (Approved)
{
  "task_id": "TASK-abc123",
  "approved": true,
  "quality_score": 0.92,
  "final_content": {
    // Enhanced and validated insight
  }
}

// L3 → L2 Message (Revision)
{
  "task_id": "TASK-abc123",
  "needs_revision": true,
  "feedback": {
    "issues": ["Missing statistical significance", "Incomplete data range"],
    "suggestions": ["Add confidence intervals", "Include prior year comparison"]
  }
}
```

## State Management

Each task maintains a `FlowState` object that tracks:
- Current level (1, 2, or 3)
- Status (pending, analyzing, generating, validating, approved, rejected)
- All draft insights generated
- Final validated insight (if approved)
- Error log
- Processing timestamps

This ensures complete traceability and debugging capability for every query processed through the system.
