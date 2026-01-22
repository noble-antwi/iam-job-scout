# Monitoring Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     IAM Job Scout Application                    │
│                        (FastAPI / Docker)                        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    main.py (FastAPI)                      │  │
│  │                                                            │  │
│  │  - Handles HTTP requests                                  │  │
│  │  - PrometheusMiddleware intercepts ALL requests           │  │
│  │  - Updates metrics automatically                          │  │
│  │  - Exposes /metrics endpoint                              │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           monitoring/ Module                              │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ middleware.py                                       │  │  │
│  │  │  • PrometheusMiddleware                            │  │  │
│  │  │  • Tracks every HTTP request                       │  │  │
│  │  │  • Measures response time                          │  │  │
│  │  │  • Counts errors automatically                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ metrics.py                                          │  │  │
│  │  │  • 25+ Prometheus metrics                          │  │  │
│  │  │  • Histograms (latency)                            │  │  │
│  │  │  • Counters (requests, errors)                     │  │  │
│  │  │  • Gauges (connections, memory)                    │  │  │
│  │  │  • Helper functions                                │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ db_metrics.py                                       │  │  │
│  │  │  • track_db_operation() context manager           │  │  │
│  │  │  • Measures DB query time                          │  │  │
│  │  │  • Counts DB operations                            │  │  │
│  │  │  • Tracks connection pool                          │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Port 5000                                                        │
│  GET /metrics  ◄─────────────────────────────────────────────┐  │
└──────────────────────────────────────────────────────────────┼──┘
                                                                │
                                                                │
                         Scrapes every 15s                      │
                                                                │
┌───────────────────────────────────────────────────────────────┼──┐
│                  Prometheus Server                            │  │
│                  192.168.60.2:9090                            │  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Time-Series Database                                    │    │
│  │  • Stores metrics history                              │    │
│  │  • Retention: 15 days (default)                        │    │
│  │  • Compression: ~1.5 bytes per sample                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Alert Manager                                           │    │
│  │  • Evaluates alert rules                               │    │
│  │  • Fires when thresholds exceeded                      │    │
│  │  • Groups and deduplicates alerts                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Port 9090                                                       │
│  /api/v1/query  ◄──────────────────────────────────────────┐   │
└─────────────────────────────────────────────────────────────┼───┘
                                                               │
                                                               │
                            Queries metrics                    │
                                                               │
┌──────────────────────────────────────────────────────────────┼──┐
│                    Grafana Server                            │  │
│                  192.168.60.2:3000                           │  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Dashboards                                              │   │
│  │  • Application Health (uptime, errors)                 │   │
│  │  • Performance (latency, throughput)                   │   │
│  │  • Business Metrics (jobs, scans)                      │   │
│  │  • Resources (DB connections, memory)                  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Alerting (optional)                                     │   │
│  │  • Email notifications                                  │   │
│  │  • Slack/Discord webhooks                              │   │
│  │  • PagerDuty integration                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Port 3000                                                      │
│  Web UI  ◄────────────────────────────────── User Access      │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Request Flow
```
User Request → FastAPI → PrometheusMiddleware → Your Code → Response
                  │
                  └─► Updates metrics:
                      • Request count +1
                      • Request duration recorded
                      • Status code tracked
                      • Errors captured
```

### 2. Metrics Collection Flow
```
Every 15 seconds:

Prometheus → HTTP GET /metrics → IAM Job Scout
                                      │
                                      └─► Returns:
                                          - All HTTP metrics
                                          - Business metrics
                                          - DB metrics
                                          - Error counters
```

### 3. Visualization Flow
```
User → Grafana Dashboard → PromQL Query → Prometheus → Returns Data
                                                            │
                                                            └─► Graph/Panel
```

## Metrics Update Schedule

```
┌─────────────────────────────────────────────────────────────┐
│ Time    │ Event                       │ Metrics Updated     │
├─────────┼─────────────────────────────┼─────────────────────┤
│ Always  │ HTTP Request arrives        │ Automatic via MW    │
│ Every   │ Scheduled metrics update    │ Business metrics    │
│ 30s     │ (update_all_metrics)        │ DB connections      │
│         │                             │ Uptime              │
│ On      │ Job scan completes          │ Scan metrics        │
│ Event   │                             │ Job counts          │
│ On      │ Job status updated          │ Status counters     │
│ Event   │                             │                     │
│ Every   │ Prometheus scrapes          │ All metrics         │
│ 15s     │ /metrics endpoint           │ exported            │
└─────────────────────────────────────────────────────────────┘
```

## Middleware Interception

```
HTTP Request Flow with PrometheusMiddleware:

Client
  │
  │ 1. Request arrives
  ▼
┌─────────────────────┐
│ PrometheusMiddleware│
│                     │
│ START:              │
│ • Start timer       │
│ • Inc in_progress   │
└──────────┬──────────┘
           │
           │ 2. Pass to app
           ▼
┌─────────────────────┐
│  Your FastAPI App   │
│  (main.py routes)   │
│                     │
│ • Process request   │
│ • Query database    │
│ • Return response   │
└──────────┬──────────┘
           │
           │ 3. Response returns
           ▼
┌─────────────────────┐
│ PrometheusMiddleware│
│                     │
│ END:                │
│ • Stop timer        │
│ • Record duration   │
│ • Inc request_total │
│ • Dec in_progress   │
│ • Track errors      │
└──────────┬──────────┘
           │
           │ 4. Response to client
           ▼
Client
```

## Database Instrumentation (Optional)

```
Your Code with DB Tracking:

┌─────────────────────────────────────────────────┐
│ def get_jobs(db):                                │
│     with track_db_operation('select', 'jobs'):  │
│         │                                        │
│         │ START:                                 │
│         │ • Start timer                          │
│         │                                        │
│         results = db.query(Job).all()           │
│         │                                        │
│         │ END:                                   │
│         │ • Stop timer                           │
│         │ • Record duration                      │
│         │ • Count operation                      │
│         │ • Track errors (if any)                │
│         │                                        │
│     return results                               │
└─────────────────────────────────────────────────┘
```

## Alert Flow

```
Prometheus Alert Evaluation:

Every 15s:
  │
  ├─► Evaluate: error_rate > 5%
  │   └─► Condition met? → PENDING (wait for: 5m)
  │       └─► Still met after 5m? → FIRING
  │           └─► Send to Alertmanager
  │               └─► Group similar alerts
  │                   └─► Send notification:
  │                       • Email
  │                       • Slack
  │                       • PagerDuty
  │
  ├─► Evaluate: service_down
  │   └─► Condition met? → PENDING (wait for: 1m)
  │       └─► Still met after 1m? → FIRING (critical!)
  │
  └─► Evaluate: slow_requests
      └─► All good → No alert
```

## The 4 Golden Signals in Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. LATENCY (How long?)                                      │
│     ▪ HTTP response time ◄── PrometheusMiddleware           │
│     ▪ DB query time      ◄── track_db_operation()           │
│     ▪ API call time      ◄── track_external_api()           │
│                                                               │
│  2. TRAFFIC (How much?)                                      │
│     ▪ Requests/second    ◄── PrometheusMiddleware           │
│     ▪ Concurrent requests◄── PrometheusMiddleware           │
│     ▪ Active users       ◄── Session tracking                │
│                                                               │
│  3. ERRORS (What failed?)                                    │
│     ▪ HTTP errors        ◄── PrometheusMiddleware           │
│     ▪ DB errors          ◄── track_db_operation()           │
│     ▪ App exceptions     ◄── Error handlers                  │
│                                                               │
│  4. SATURATION (How full?)                                   │
│     ▪ DB connections     ◄── update_connection_pool_metrics()│
│     ▪ Memory usage       ◄── Process metrics                 │
│     ▪ Request queue      ◄── In-progress gauge               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Files and Their Roles

```
Your Project Structure:

iam-job-scout/
│
├── monitoring/                    ← NEW! Monitoring module
│   ├── __init__.py               → Exports all metrics
│   ├── metrics.py                → Defines 25+ metrics
│   ├── middleware.py             → Auto HTTP tracking
│   ├── db_metrics.py             → DB instrumentation
│   └── README.md                 → Module documentation
│
├── main.py                        ← UPDATED! Uses monitoring
│   ├── Imports monitoring module
│   ├── Adds PrometheusMiddleware
│   ├── Schedules metrics updates
│   └── Exposes /metrics endpoint
│
├── MONITORING_QUICKSTART.md      ← START HERE! (10 min setup)
├── MONITORING.md                 ← Full guide (deep dive)
├── MONITORING_SUMMARY.md         ← What changed summary
├── prometheus.yml.example        ← Copy to Prometheus server
├── prometheus-alerts.yml.example ← Copy to Prometheus server
│
└── [rest of your app]            ← Unchanged (no updates needed)
```

## Quick Reference: Metric Types

```
┌──────────┬──────────────────┬─────────────────────────────┐
│ Type     │ Use Case         │ Example                     │
├──────────┼──────────────────┼─────────────────────────────┤
│ Counter  │ Things that      │ http_requests_total         │
│          │ only go up       │ Increases: .inc()           │
│          │                  │ Query: rate()               │
├──────────┼──────────────────┼─────────────────────────────┤
│ Gauge    │ Things that      │ db_connections_active       │
│          │ go up and down   │ Set value: .set(10)         │
│          │                  │ Query: current value        │
├──────────┼──────────────────┼─────────────────────────────┤
│ Histogram│ Distribution     │ http_request_duration       │
│          │ of values        │ Observe: .observe(0.5)      │
│          │ (percentiles)    │ Query: histogram_quantile() │
└──────────┴──────────────────┴─────────────────────────────┘
```

---

**Visual Reference**: Keep this diagram handy while setting up!
