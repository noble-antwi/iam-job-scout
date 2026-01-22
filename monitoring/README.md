# Monitoring Overview

## New Monitoring Structure

```
monitoring/
├── __init__.py          # Module exports
├── metrics.py           # All Prometheus metrics definitions
├── middleware.py        # Automatic HTTP request tracking
└── db_metrics.py        # Database instrumentation utilities
```

## What Changed

### Before (Old Setup)
- Metrics defined in main.py (mixed concerns)
- Only updated during scans (stale data)
- Limited metrics (only business metrics)
- No automatic HTTP tracking
- No database performance tracking

### After (New Setup)
- Organized monitoring module (separation of concerns)
- Metrics updated every 30 seconds (fresh data)
- Comprehensive metrics (4 Golden Signals)
- Automatic HTTP request tracking via middleware
- Database query tracking with decorators
- External API monitoring utilities
- Error tracking with context

## Metrics Categories

### 1. Latency (How long things take)
- `http_request_duration_seconds` - HTTP response times
- `db_query_duration_seconds` - Database query duration
- `external_api_duration_seconds` - External API call duration
- `scan_duration_seconds` - Job scan duration

### 2. Traffic (Request volume)
- `http_requests_total` - Total HTTP requests
- `http_requests_in_progress` - Concurrent requests
- `active_user_sessions` - Active users
- `external_api_requests_total` - API call count

### 3. Errors (Failure rates)
- `application_errors_total` - Application errors
- `database_errors_total` - Database errors
- `external_api_errors_total` - API failures
- `scan_errors_total` - Scan failures

### 4. Saturation (Resource usage)
- `db_connections_active` - Active DB connections
- `db_connections_idle` - Idle DB connections
- `process_memory_bytes` - Memory usage
- `application_uptime_seconds` - Uptime

### 5. Business Metrics
- `iam_jobs_total` - Total jobs
- `iam_jobs_new_this_week` - New jobs
- `iam_jobs_saved` - Saved jobs
- `iam_jobs_applied` - Applied jobs
- `iam_scan_runs_total` - Scan count by status
- `iam_last_successful_scan_timestamp` - Last scan time

## How to Use

### View Metrics
```bash
curl http://localhost:5000/metrics
```

### Automatic Tracking
HTTP requests are **automatically tracked** by middleware. No code changes needed!

### Track Database Operations (Optional)
```python
from monitoring.db_metrics import track_db_operation

def get_jobs(self, db):
    with track_db_operation('select', 'jobs'):
        return db.query(Job).all()
```

### Track External APIs (Optional)
```python
from monitoring.metrics import track_external_api

async def call_api():
    with track_external_api('jsearch', '/search'):
        response = await httpx.get(url)
        return response.json()
```

## Documentation

- **Quick Start**: [../docs/MONITORING_QUICKSTART.md](../docs/MONITORING_QUICKSTART.md) - Get monitoring running in 10 minutes
- **Full Guide**: [../docs/MONITORING.md](../docs/MONITORING.md) - Comprehensive documentation
- **Prometheus Config**: [../docs/prometheus.yml.example](../docs/prometheus.yml.example) - Copy to your Prometheus server
- **Alert Rules**: [../docs/prometheus-alerts.yml.example](../docs/prometheus-alerts.yml.example) - Production-ready alerts

## Setup Checklist

- [ ] Application running with new monitoring code
- [ ] Prometheus configured to scrape `/metrics`
- [ ] Grafana connected to Prometheus
- [ ] Basic dashboard created
- [ ] Alert rules deployed
- [ ] Alertmanager configured (optional)

## Testing

```bash
# 1. Check metrics endpoint
curl http://localhost:5000/metrics

# 2. Generate test traffic
for i in {1..100}; do curl http://localhost:5000/ & done

# 3. Check Prometheus targets
# Visit: http://192.168.60.2:9090/targets

# 4. View in Grafana
# Visit: http://192.168.60.2:3000
```

## Key Dashboards to Create

1. **Application Health** - Uptime, error rate, request rate
2. **Performance** - Response time, DB queries, API calls
3. **Business Metrics** - Jobs, scans, user activity
4. **Resources** - Connections, memory, saturation

## Recommended Alerts

1. Service Down (critical)
2. Error Rate > 5% (warning)
3. Response Time p95 > 2s (warning)
4. No scan in 24 hours (warning)
5. DB connections > 80% (warning)

## Learning Resources

- [Google SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
- [4 Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals)

## Support

Questions? Check the documentation or review the code in `monitoring/` directory.

---

**Next Steps:** Follow [MONITORING_QUICKSTART.md](MONITORING_QUICKSTART.md) to set up Prometheus and Grafana.
