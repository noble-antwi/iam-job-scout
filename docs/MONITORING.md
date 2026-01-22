# IAM Job Scout - Monitoring Guide

This guide explains the monitoring setup for IAM Job Scout, following industry best practices and the **4 Golden Signals** of monitoring.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [The 4 Golden Signals](#the-4-golden-signals)
3. [Available Metrics](#available-metrics)
4. [Setting Up Prometheus](#setting-up-prometheus)
5. [Creating Grafana Dashboards](#creating-grafana-dashboards)
6. [Instrumenting Your Code](#instrumenting-your-code)
7. [Alerting Rules](#alerting-rules)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Monitoring Stack

```
┌─────────────────┐
│ IAM Job Scout   │ ──► Exposes /metrics endpoint
│ (FastAPI App)   │     with Prometheus format
└────────┬────────┘
         │
         │ Scrapes every 15s
         ▼
┌─────────────────┐
│   Prometheus    │ ──► Stores time-series data
│  192.168.60.2   │     Evaluates alert rules
│    :9090        │
└────────┬────────┘
         │
         │ Queries
         ▼
┌─────────────────┐
│    Grafana      │ ──► Visualizes metrics
│  192.168.60.2   │     Shows dashboards
│    :3000        │     Sends alerts
└─────────────────┘
```

### Components

1. **Application (`main.py`)**: Exposes metrics at `/metrics`
2. **PrometheusMiddleware**: Automatically tracks HTTP requests
3. **Metrics Module** (`monitoring/`): Defines and updates metrics
4. **Prometheus**: Scrapes and stores metrics
5. **Grafana**: Visualizes metrics in dashboards

---

## The 4 Golden Signals

Google's Site Reliability Engineering (SRE) book identifies these as the most important metrics:

### 1. **Latency** 
*How long does it take to service a request?*

**Metrics:**
- `http_request_duration_seconds` - HTTP response time
- `db_query_duration_seconds` - Database query time
- `external_api_duration_seconds` - External API call time
- `scan_duration_seconds` - Job scan duration

**Why it matters:** Slow responses = poor user experience

**Alert on:** p95 latency > 2 seconds

### 2. **Traffic**
*How much demand is being placed on your system?*

**Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_requests_in_progress` - Concurrent requests
- `active_user_sessions` - Active users
- `external_api_requests_total` - API call volume

**Why it matters:** Helps capacity planning and detecting unusual patterns

**Alert on:** Sudden drops (service down) or spikes (attack)

### 3. **Errors**
*What is the rate of requests that are failing?*

**Metrics:**
- `application_errors_total` - Application errors
- `database_errors_total` - Database errors
- `external_api_errors_total` - API call failures
- `scan_errors_total` - Job scan failures

**Why it matters:** Errors = broken functionality

**Alert on:** Error rate > 5%

### 4. **Saturation**
*How "full" is your service?*

**Metrics:**
- `db_connections_active` - Active DB connections
- `process_memory_bytes` - Memory usage
- `application_uptime_seconds` - How long app has been running

**Why it matters:** Predicts when you'll run out of resources

**Alert on:** Connection pool > 80% full, Memory > 90% used

---

## Available Metrics

### Application Performance Metrics

#### HTTP Request Duration (Histogram)
```promql
# Name: http_request_duration_seconds
# Labels: method, endpoint, status_code

# Example queries:
# Average response time across all endpoints
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Slow endpoints (p95 > 1s)
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket{endpoint!="/metrics"}[5m])
) > 1
```

#### HTTP Requests Total (Counter)
```promql
# Name: http_requests_total
# Labels: method, endpoint, status_code

# Example queries:
# Request rate (requests per second)
rate(http_requests_total[5m])

# Error rate percentage
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / 
sum(rate(http_requests_total[5m])) * 100

# Most popular endpoints
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))
```

#### HTTP Requests In Progress (Gauge)
```promql
# Name: http_requests_in_progress
# Labels: method, endpoint

# Example queries:
# Current concurrent requests
sum(http_requests_in_progress)

# Concurrent requests by endpoint
sum by (endpoint) (http_requests_in_progress)
```

### Business Metrics

#### Jobs Metrics (Gauges)
```promql
# Total jobs in database
iam_jobs_total

# New jobs this week
iam_jobs_new_this_week

# Saved jobs
iam_jobs_saved

# Applied jobs
iam_jobs_applied

# Example: Job growth rate
rate(iam_jobs_total[1d]) * 86400  # Jobs added per day
```

#### Scan Metrics
```promql
# Scan success rate (%)
sum(rate(iam_scan_runs_total{status="success"}[1h])) / 
sum(rate(iam_scan_runs_total[1h])) * 100

# Time since last successful scan (seconds)
time() - iam_last_successful_scan_timestamp

# Average scan duration
rate(scan_duration_seconds_sum[1h]) / rate(scan_duration_seconds_count[1h])

# Jobs found per scan
iam_scan_jobs_found_last
```

### Database Metrics

#### Query Duration (Histogram)
```promql
# Name: db_query_duration_seconds
# Labels: operation, table

# Average query time by operation
rate(db_query_duration_seconds_sum[5m]) / 
rate(db_query_duration_seconds_count[5m])

# Slow queries (p95 > 100ms)
histogram_quantile(0.95, 
  rate(db_query_duration_seconds_bucket[5m])
) > 0.1
```

#### Database Operations (Counter)
```promql
# Name: db_operations_total
# Labels: operation, table, status

# Query rate by table
sum by (table) (rate(db_operations_total[5m]))

# Failed database operations
sum(rate(db_operations_total{status="error"}[5m]))
```

#### Connection Pool (Gauges)
```promql
# Active connections
db_connections_active

# Idle connections
db_connections_idle

# Connection pool utilization (%)
db_connections_active / (db_connections_active + db_connections_idle) * 100
```

### External API Metrics

```promql
# API call duration
rate(external_api_duration_seconds_sum[5m]) / 
rate(external_api_duration_seconds_count[5m])

# API error rate
sum(rate(external_api_errors_total[5m])) by (api_name)

# API success rate
sum(rate(external_api_requests_total{status="success"}[5m])) / 
sum(rate(external_api_requests_total[5m])) * 100
```

---

## Setting Up Prometheus

### Step 1: Configure Prometheus to Scrape Your App

Edit your Prometheus configuration file (usually `/etc/prometheus/prometheus.yml`):

```yaml
global:
  scrape_interval: 15s      # Scrape every 15 seconds
  evaluation_interval: 15s  # Evaluate rules every 15 seconds

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # IAM Job Scout application
  - job_name: 'iam-job-scout'
    static_configs:
      - targets: ['<YOUR_APP_HOST_IP>:5000']  # Replace with your app's IP
        labels:
          app: 'iam-job-scout'
          environment: 'production'
          instance: 'web-1'
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Step 2: Find Your Application's IP Address

On your Docker host, run:
```bash
# If using docker-compose
docker inspect iam-job-scout-web-1 | grep IPAddress

# Or use host network
# In your docker-compose.yml, use: network_mode: "host"
# Then target: 'localhost:5000'
```

### Step 3: Reload Prometheus Configuration

```bash
# Send reload signal to Prometheus
curl -X POST http://192.168.60.2:9090/-/reload

# Or restart Prometheus
sudo systemctl restart prometheus
```

### Step 4: Verify Targets

1. Open Prometheus UI: `http://192.168.60.2:9090`
2. Go to **Status** → **Targets**
3. Check that `iam-job-scout` target is **UP** (green)

If it shows **DOWN**:
- Check firewall rules
- Verify the IP address is correct
- Ensure the app is running: `docker ps`
- Test metrics endpoint: `curl http://<app-ip>:5000/metrics`

---

## Creating Grafana Dashboards

### Step 1: Add Prometheus Data Source

1. Open Grafana: `http://192.168.60.2:3000`
2. Go to **Configuration** (gear icon) → **Data Sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Set URL: `http://localhost:9090` (if on same server)
6. Click **Save & Test**

### Step 2: Create a New Dashboard

1. Click **+** → **Dashboard**
2. Click **Add new panel**

### Step 3: Essential Panels to Create

#### Panel 1: Request Rate
```
Type: Graph
Query: rate(http_requests_total{job="iam-job-scout"}[5m])
Legend: {{method}} {{endpoint}}
Title: HTTP Requests per Second
```

#### Panel 2: Response Time (p95)
```
Type: Graph
Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="iam-job-scout"}[5m]))
Legend: {{endpoint}}
Title: Response Time (95th percentile)
Unit: seconds (s)
```

#### Panel 3: Error Rate
```
Type: Stat (big number)
Query: sum(rate(http_requests_total{job="iam-job-scout",status_code=~"5.."}[5m])) / sum(rate(http_requests_total{job="iam-job-scout"}[5m])) * 100
Title: Error Rate %
Unit: percent (0-100)
Thresholds: Green <1, Yellow <5, Red >=5
```

#### Panel 4: Total Jobs
```
Type: Stat
Query: iam_jobs_total
Title: Total Jobs in Database
```

#### Panel 5: New Jobs This Week
```
Type: Stat
Query: iam_jobs_new_this_week
Title: New Jobs (7 days)
Color: Green
```

#### Panel 6: Scan Success Rate
```
Type: Gauge
Query: sum(rate(iam_scan_runs_total{status="success"}[1h])) / sum(rate(iam_scan_runs_total[1h])) * 100
Title: Scan Success Rate
Unit: percent (0-100)
Min: 0, Max: 100
Thresholds: Red <80, Yellow <95, Green >=95
```

#### Panel 7: Time Since Last Scan
```
Type: Stat
Query: (time() - iam_last_successful_scan_timestamp) / 3600
Title: Hours Since Last Successful Scan
Unit: hours (h)
Thresholds: Green <6, Yellow <24, Red >=24
```

#### Panel 8: Database Query Performance
```
Type: Graph
Query: rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m])
Legend: {{operation}} on {{table}}
Title: Average DB Query Duration
Unit: seconds (s)
```

#### Panel 9: Active Database Connections
```
Type: Gauge
Query: db_connections_active
Title: Active DB Connections
Max: <your_pool_size>  # e.g., 20
Thresholds: Green <10, Yellow <16, Red >=16
```

#### Panel 10: Uptime
```
Type: Stat
Query: application_uptime_seconds / 86400
Title: Uptime
Unit: days
```

### Step 4: Organize Your Dashboard

Create rows for different categories:
- **Application Health** (uptime, error rate, request rate)
- **Performance** (response time, DB queries, API calls)
- **Business Metrics** (jobs, scans, user activity)
- **Resources** (connections, memory, requests in progress)

### Step 5: Save Dashboard

1. Click the disk icon (Save dashboard)
2. Name it: "IAM Job Scout - Overview"
3. Click **Save**

### Advanced: Import Ready-Made Dashboards

For standard metrics, you can import pre-built dashboards:
1. Go to **+** → **Import**
2. Enter dashboard ID:
   - **1860** - Node Exporter Full (system metrics)
   - **12708** - FastAPI Observability
3. Select your Prometheus data source
4. Click **Import**

---

## Instrumenting Your Code

### Tracking Database Operations

In your `jobs/job_service.py`, add tracking:

```python
from monitoring.db_metrics import track_db_operation

class JobService:
    def get_all_jobs(self, db):
        with track_db_operation('select', 'jobs'):
            return db.query(Job).all()
    
    def create_job(self, db, job_data):
        with track_db_operation('insert', 'jobs'):
            job = Job(**job_data)
            db.add(job)
            db.commit()
            return job
```

### Tracking External API Calls

When calling external APIs:

```python
from monitoring.metrics import track_external_api

async def search_jobs_api(query: str):
    with track_external_api('jsearch', '/search'):
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params={'query': query})
            return response.json()
```

### Manual Metric Updates

For custom business logic:

```python
from monitoring.metrics import JOB_STATUS_UPDATES

def mark_job_applied(job_id: int):
    # Your logic
    job.status = 'applied'
    db.commit()
    
    # Update metric
    JOB_STATUS_UPDATES.labels(status='applied').inc()
```

---

## Alerting Rules

### Configure Prometheus Alerts

Create `/etc/prometheus/rules/iam_job_scout.yml`:

```yaml
groups:
  - name: iam_job_scout_alerts
    interval: 30s
    rules:
      # Service down
      - alert: ServiceDown
        expr: up{job="iam-job-scout"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "IAM Job Scout is down"
          description: "Service has been down for more than 1 minute"

      # High error rate
      - alert: HighErrorRate
        expr: |
          (sum(rate(http_requests_total{job="iam-job-scout",status_code=~"5.."}[5m])) 
          / sum(rate(http_requests_total{job="iam-job-scout"}[5m]))) * 100 > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanize }}%"

      # Slow response time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket{job="iam-job-scout"}[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times"
          description: "p95 latency is {{ $value | humanize }}s"

      # No successful scan in 24 hours
      - alert: NoRecentScan
        expr: (time() - iam_last_successful_scan_timestamp) > 86400
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "No successful job scan in 24 hours"
          description: "Last successful scan was {{ $value | humanizeDuration }} ago"

      # Scan failures
      - alert: ScanFailures
        expr: rate(iam_scan_runs_total{status="failed"}[1h]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Job scans are failing"
          description: "{{ $value }} scans failed in the last hour"

      # Database connection pool near capacity
      - alert: DatabaseConnectionsSaturated
        expr: |
          db_connections_active / 
          (db_connections_active + db_connections_idle) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly full"
          description: "Connection pool is {{ $value | humanize }}% utilized"

      # High memory usage (if you add process metrics)
      - alert: HighMemoryUsage
        expr: process_memory_bytes > 1000000000  # 1GB
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizeBytes }}"
```

Reference this in your `prometheus.yml`:

```yaml
rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']  # If using Alertmanager
```

---

## Troubleshooting

### Metrics Not Showing in Prometheus

**Check endpoint is accessible:**
```bash
curl http://<app-ip>:5000/metrics
```

**Check Prometheus logs:**
```bash
tail -f /var/log/prometheus/prometheus.log
```

**Verify scrape configuration:**
```bash
# Check if target is configured
curl http://192.168.60.2:9090/api/v1/targets | jq
```

### No Data in Grafana

**Test Prometheus query:**
1. Go to Prometheus UI: http://192.168.60.2:9090
2. Click "Graph"
3. Enter query: `up{job="iam-job-scout"}`
4. Click "Execute"
5. Should show value `1`

**Check Grafana data source:**
1. Configuration → Data Sources → Prometheus
2. Click "Test"
3. Should show "Data source is working"

### Metrics Stuck at Zero

**Trigger some activity:**
```bash
# Generate traffic
for i in {1..100}; do curl http://<app-ip>:5000/; done

# Run a scan
curl -X POST http://<app-ip>:5000/admin/run-scan \
  -H "X-Admin-Token: your-token"
```

**Check middleware is active:**
- Look for log entries about slow requests
- Check that `http_requests_total` increments

### High Cardinality Warning

If you see warnings about too many metrics:

**Bad:** Using user IDs or job IDs in labels
```python
# DON'T DO THIS
METRIC.labels(user_id=user_id, job_id=job_id).inc()
```

**Good:** Using categories
```python
# DO THIS
METRIC.labels(status=status, operation=operation).inc()
```

**Rule of thumb:** Keep unique label combinations < 1000

---

## Next Steps

1. Verify `/metrics` endpoint works
2. Configure Prometheus to scrape your app
3. Create basic Grafana dashboard
4. Set up critical alerts
5. Add system metrics with Node Exporter
6. Configure Alertmanager for notifications
7. Create runbooks for each alert

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
- [SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Questions?** Check the logs or review the code in `monitoring/` directory.
