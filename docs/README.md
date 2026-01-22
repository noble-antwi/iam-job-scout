# IAM Job Scout - Documentation

Complete documentation for monitoring, deployment, and operations.

## 📚 Documentation Index

### Monitoring & Observability

| Document | Description | When to Use |
|----------|-------------|-------------|
| **[MONITORING_QUICKSTART.md](MONITORING_QUICKSTART.md)** | 10-minute setup guide | First-time setup |
| **[MONITORING.md](MONITORING.md)** | Complete monitoring guide | Reference & deep dive |
| **[MONITORING_SUMMARY.md](MONITORING_SUMMARY.md)** | What changed overview | Understanding the refactor |
| **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** | Visual architecture guide | Understanding the system |

### Configuration Files

| File | Description | Usage |
|------|-------------|-------|
| **[prometheus.yml.example](prometheus.yml.example)** | Prometheus config template | Copy to Prometheus server |
| **[prometheus-alerts.yml.example](prometheus-alerts.yml.example)** | Production-ready alert rules | Copy to Prometheus server |

### Infrastructure

| Document | Description | When to Use |
|----------|-------------|-------------|
| **[DOCKER_IP_GUIDE.md](DOCKER_IP_GUIDE.md)** | Docker networking guide | Docker deployment issues |

---

## 🚀 Quick Links

### Getting Started
1. [10-Minute Monitoring Setup](MONITORING_QUICKSTART.md)
2. [Docker IP Configuration](DOCKER_IP_GUIDE.md)

### Reference
- [Complete Monitoring Guide](MONITORING.md)
- [System Architecture](ARCHITECTURE_DIAGRAM.md)
- [What Was Changed](MONITORING_SUMMARY.md)

### Configuration
- [Prometheus Configuration](prometheus.yml.example)
- [Alert Rules](prometheus-alerts.yml.example)

---

## 📊 Monitoring Overview

IAM Job Scout includes production-grade monitoring with:

- **25+ Prometheus metrics** following the 4 Golden Signals
- **Automatic HTTP tracking** via middleware
- **Business metrics** for job counts and scan performance
- **Database performance** tracking
- **Ready-to-use Grafana dashboards**

### Key Metrics Available

```
# Application Performance
http_request_duration_seconds
http_requests_total
http_requests_in_progress

# Business Metrics
iam_jobs_total
iam_jobs_new_this_week
iam_jobs_saved
iam_jobs_applied
iam_scan_runs_total

# Database
db_query_duration_seconds
db_connections_active

# System
application_uptime_seconds
process_memory_bytes
```

---

## 🎯 Common Tasks

### Setting Up Monitoring
→ Start here: [MONITORING_QUICKSTART.md](MONITORING_QUICKSTART.md)

### Troubleshooting Docker Networking
→ Read: [DOCKER_IP_GUIDE.md](DOCKER_IP_GUIDE.md)

### Creating Grafana Dashboards
→ See: [MONITORING.md - Creating Grafana Dashboards](MONITORING.md#creating-grafana-dashboards)

### Understanding the Architecture
→ View: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)

### Setting Up Alerts
→ Use: [prometheus-alerts.yml.example](prometheus-alerts.yml.example)

---

## 🆘 Support

For issues or questions:
1. Check the relevant guide above
2. Review [MONITORING.md](MONITORING.md) troubleshooting section
3. Open a GitHub issue

---

**Back to [Main README](../README.md)**
