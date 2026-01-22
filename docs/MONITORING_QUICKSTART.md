# Quick Start: Monitoring Setup

This guide gets you up and running with monitoring in 10 minutes.

## ✅ Prerequisites

- Your Prometheus server at `http://192.168.60.2:9090/`
- Your Grafana server at `http://192.168.60.2:3000/`
- IAM Job Scout running in Docker

## 📋 Step-by-Step Setup

### Step 1: Find Your Application's IP Address (2 min)

On your Docker host machine:

```bash
# Method 1: Use Docker Host IP (RECOMMENDED - Most Stable)
hostname -I | awk '{print $1}'
# Example output: 192.168.1.100
# This IP stays the same even when containers restart!

# Method 2: Get container IP (NOT RECOMMENDED - Changes on restart!)
docker inspect iam-job-scout-web-1 | grep IPAddress
# Example output: 172.18.0.2
# ⚠️  WARNING: This IP WILL CHANGE when container restarts!

# Method 3: Test it works from Prometheus server
curl http://<YOUR_IP>:5000/health
```

**💡 Which IP to Use?**
- ✅ **Use Host IP** (Method 1) - Stable, doesn't change
- ❌ **Avoid Container IP** (Method 2) - Changes on every restart

**Save this IP address** - you'll need it next.

### Step 2: Test Metrics Endpoint (1 min)

```bash
# Should return Prometheus metrics
curl http://<YOUR_APP_IP>:5000/metrics

# Look for lines like:
# http_requests_total{...} 123
# iam_jobs_total 456
```

If this doesn't work:
- Check Docker container is running: `docker ps`
- Check port 5000 is exposed: `docker port iam-job-scout-web-1`
- Check firewall: `sudo ufw allow 5000`

### Step 3: Configure Prometheus (3 min)

**On your Prometheus server (192.168.60.2):**

```bash
# 1. Edit Prometheus config
sudo nano /etc/prometheus/prometheus.yml

# 2. Add this to the scrape_configs section:
```

```yaml
  - job_name: 'iam-job-scout'
    static_configs:
      - targets: ['<YOUR_APP_IP>:5000']  # Replace with actual IP
        labels:
          app: 'iam-job-scout'
          environment: 'production'
    metrics_path: '/metrics'
    scrape_interval: 15s
```

```bash
# 3. Validate config
promtool check config /etc/prometheus/prometheus.yml

# 4. Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# OR
sudo systemctl reload prometheus
```

### Step 4: Verify in Prometheus (2 min)

1. Open browser: `http://192.168.60.2:9090`
2. Go to **Status** → **Targets**
3. Find `iam-job-scout` job
4. Status should show **UP** (green)

**If DOWN (red):**
- Check IP address is correct
- Ping from Prometheus server: `ping <YOUR_APP_IP>`
- Test metrics from Prometheus server: `curl http://<YOUR_APP_IP>:5000/metrics`
- Check firewall rules

**Test a query:**
1. Go to **Graph** tab
2. Enter: `iam_jobs_total`
3. Click **Execute**
4. Should show current job count

### Step 5: Create Basic Grafana Dashboard (5 min)

**On Grafana (192.168.60.2:3000):**

#### 5a. Add Data Source (if not already done)

1. Click **⚙️ Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. URL: `http://localhost:9090` (or `http://192.168.60.2:9090`)
5. Click **Save & Test**

#### 5b. Create Dashboard

1. Click **+** → **Dashboard**
2. Click **Add new panel**

#### Panel 1: Total Jobs
```
Query: iam_jobs_total
Visualization: Stat (big number)
Title: Total Jobs in Database
```
Click **Apply**

#### Panel 2: Request Rate
```
Query: rate(http_requests_total{job="iam-job-scout"}[5m])
Visualization: Time series (graph)
Title: Requests per Second
Legend: {{endpoint}}
```
Click **Apply**

#### Panel 3: Error Rate
```
Query: (sum(rate(http_requests_total{job="iam-job-scout",status_code=~"5.."}[5m])) / sum(rate(http_requests_total{job="iam-job-scout"}[5m]))) * 100
Visualization: Stat
Title: Error Rate %
Unit: Percent (0-100)
Thresholds: Base=green, 1=yellow, 5=red
```
Click **Apply**

#### Save Dashboard
1. Click **💾 Save dashboard** (top right)
2. Name: `IAM Job Scout - Overview`
3. Click **Save**

## 🎉 Done! What's Next?

### View Your Metrics

- **Prometheus:** `http://192.168.60.2:9090/graph`
- **Grafana:** `http://192.168.60.2:3000/dashboards`

### Test It Works

Generate some traffic:
```bash
# From any machine that can reach your app
for i in {1..100}; do 
    curl http://<YOUR_APP_IP>:5000/ &
done
```

Watch the metrics update in Grafana (refresh after 30 seconds).

### Key Metrics to Watch

| Metric | What It Means | Good Value |
|--------|---------------|------------|
| `iam_jobs_total` | Total jobs in DB | Growing over time |
| `iam_jobs_new_this_week` | New jobs last 7 days | > 0 |
| `rate(http_requests_total[5m])` | Requests/sec | Depends on traffic |
| Error rate | % of failed requests | < 1% |
| Response time p95 | 95% requests faster than | < 1 second |
| `iam_last_successful_scan_timestamp` | Last scan time | < 24 hours ago |

## 🔍 Troubleshooting

### "No data" in Grafana

```bash
# Test query in Prometheus first
# Go to: http://192.168.60.2:9090/graph
# Query: up{job="iam-job-scout"}
# Should show: 1

# If shows 0 or no data:
# - Check Prometheus targets
# - Verify IP address
# - Check firewall
```

### Metrics stuck at zero

```bash
# Generate activity
curl http://<YOUR_APP_IP>:5000/
curl http://<YOUR_APP_IP>:5000/health
curl http://<YOUR_APP_IP>:5000/api/stats

# Check metrics updated
curl http://<YOUR_APP_IP>:5000/metrics | grep http_requests_total
```

### Can't access metrics endpoint

```bash
# Check app is running
docker ps | grep iam-job-scout

# Check app logs
docker logs iam-job-scout-web-1 --tail 50

# Restart app if needed
docker-compose restart web
```

### Target goes DOWN after container restart

**Problem:** Prometheus shows target as DOWN after restarting containers.

**Cause:** You used the container IP (172.18.0.x) which changed on restart.

**Solution:**
```bash
# 1. Use your Docker HOST IP instead
hostname -I | awk '{print $1}'
# Example: 192.168.1.100

# 2. Update Prometheus config with HOST IP
sudo nano /etc/prometheus/prometheus.yml
# Change: targets: ['172.18.0.2:5000']
# To:     targets: ['192.168.1.100:5000']  # Your actual host IP

# 3. Reload Prometheus
curl -X POST http://192.168.60.2:9090/-/reload
```

**Why this works:** Port 5000 is mapped from container to host, so host IP always works.

## 📚 Next Steps

1. ✅ **Done!** Basic monitoring working
2. 📖 Read [MONITORING.md](MONITORING.md) for detailed guide
3. 🚨 Set up alerts: Copy `prometheus-alerts.yml.example`
4. 📊 Create more dashboards (see examples in MONITORING.md)
5. 🔔 Configure Alertmanager for notifications
6. 📈 Add Node Exporter for system metrics

## 🆘 Need Help?

Check the full documentation:
- **Full Guide:** [MONITORING.md](MONITORING.md)
- **Prometheus Config:** [prometheus.yml.example](prometheus.yml.example)
- **Alert Rules:** [prometheus-alerts.yml.example](prometheus-alerts.yml.example)

---

**Tip:** Bookmark your Grafana dashboard for easy access!
