# Monitoring and Logging

This document outlines the monitoring and logging strategy for the VENDORA platform.

## Monitoring with Prometheus and Grafana

The platform utilizes Prometheus for metrics collection and Grafana for visualization.

### Key Metrics Exposed

**1. FastAPI Application Metrics (via `prometheus-fastapi-instrumentator`):**
   - `fastapi_requests_total`: Counter for total HTTP requests (labels: `method`, `handler`, `status_code`).
   - `fastapi_requests_inprogress`: Gauge for current in-progress HTTP requests (labels: `method`, `handler`).
   - `fastapi_request_duration_seconds`: Histogram for HTTP request latencies (labels: `method`, `handler`).
   - `fastapi_response_size_bytes`: Summary for HTTP response sizes (labels: `method`, `handler`).
   - `fastapi_request_size_bytes`: Summary for HTTP request sizes (labels: `method`, `handler`).
   These are exposed on the `/metrics` endpoint of the main FastAPI application.

**2. Hierarchical Flow Manager Metrics (Custom):**
   - `vendora_active_flows`: Gauge indicating the number of currently active hierarchical flows.
   - `vendora_flow_processing_duration_seconds`: Histogram tracking the processing duration of hierarchical flows.
   - `vendora_flow_status_total`: Counter for the total number of flows by their final status (labels: `status`, `complexity`).
   - `vendora_cache_hits_total`: Counter for total cache hits in the flow manager.
   - `vendora_cache_misses_total`: Counter for total cache misses in the flow manager.
   These are also exposed on the `/metrics` endpoint.

**3. Existing Metrics:**
   The system also exposes other business-specific metrics like `vendora_queries_total`, `vendora_insights_approved_total`, etc., which are defined in the Prometheus configuration and Grafana dashboard.

### Grafana Dashboards

A pre-configured Grafana dashboard named "VENDORA Platform Dashboard" (UID: `vendora-main`) is available. It can be found in `monitoring/grafana/vendora-dashboard.json`.
This dashboard includes panels for:
   - Query processing rates and times.
   - Approval rates.
   - Active agents and query complexity.
   - Agent performance.
   - **New:** API Request Rate and Latency (from FastAPI).
   - **New:** Active Hierarchical Flows.
   - **New:** Flow Processing Duration (Histogram).
   - **New:** Flow Status Overview.
   - **New:** Cache Hit/Miss Rate.
   - Recent errors (from logs, if Loki or a similar log source is configured in Grafana).
   - Active alerts.

To access Grafana, refer to your deployment-specific URL for Grafana and import the dashboard JSON if it's not already set up.

### Prometheus Configuration

Prometheus is configured via `monitoring/prometheus.yml`. It scrapes metrics from:
   - `vendora-app:5001/metrics` (for FastAPI and custom application metrics).
   - `vendora-app:5001/api/v1/system/metrics` (for legacy system metrics, though most relevant metrics are now on `/metrics`).
   - `node-exporter:9100` (for system-level metrics of the host).

### Alerts

Alerts are defined in `monitoring/alerts.yml` and managed by Prometheus Alertmanager. Key new alerts include:
   - `HighFastAPIErrorRate5xx`: High rate of 5xx errors on FastAPI endpoints.
   - `HighFastAPIRequestLatency`: High p95 latency on FastAPI endpoints.
   - `LowCacheHitRate`: Cache hit rate for hierarchical flows is below a defined threshold.
   - `HighNumberOfActiveFlows`: Number of active flows is too high for too long.
   - `NoRecentSuccessfulFlows`: No flows have completed successfully in a defined period.

Refer to `alerts.yml` for specific conditions and thresholds.

## Centralized Logging with Google Cloud Logging

The application uses `structlog` for structured logging, configured to send logs directly to Google Cloud Logging.

### Log Format and Content

Logs are formatted as JSON and automatically include:
   - Timestamp (`timestamp`).
   - Log level (`level`).
   - Logger name (`logger`).
   - Log event/message (`event`).
   - Request ID (`request_id`): Automatically added to logs within an HTTP request context.
   - Google Cloud Trace ID (`trace_id`), Span ID (`span_id`), and Trace Sampled (`trace_sampled`): Automatically added if the `X-Cloud-Trace-Context` header is present in the incoming request. This links logs to traces in Google Cloud Trace.
   - Stack traces and exception information for errors.

### Accessing Logs

Logs can be accessed and queried via the Google Cloud Console's "Logs Explorer".
You can filter logs by:
   - `logName` (e.g., `projects/YOUR_PROJECT_ID/logs/vendora-fastapi-app-structlog`)
   - `jsonPayload.request_id`
   - `logging.googleapis.com/trace`
   - `jsonPayload.level` (e.g., ERROR, WARNING, INFO)
   - Free-text search within `jsonPayload.event`.

Example Query in Logs Explorer:
```
resource.type="k8s_container" # Or your specific resource type
resource.labels.container_name="vendora-app" # Or your container name
jsonPayload.request_id="your-specific-request-id"
```

Or to find all error logs:
```
resource.type="k8s_container"
resource.labels.container_name="vendora-app"
jsonPayload.level="ERROR"
```

### Correlation IDs

- **Request ID**: Each HTTP request is assigned a unique `X-Request-ID` (or uses an existing one from headers). This ID is logged with every message related to that request, allowing easy tracing of a single request's lifecycle through the system.
- **Trace ID**: If running in a GCP environment that supports tracing (like Cloud Run, GKE with Istio/Anthos Service Mesh), the `X-Cloud-Trace-Context` header will be propagated, and logs will be automatically correlated with traces in Google Cloud Trace.

This setup provides a comprehensive view of application performance and behavior, aiding in debugging and operational monitoring.
