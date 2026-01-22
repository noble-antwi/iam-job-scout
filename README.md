# IAM Job Scout

A web-based job board that helps junior to mid-level professionals find Identity & Access Management (IAM) jobs across the USA. It automatically searches for job postings using Google Custom Search Engine and displays them in a clean, searchable interface.

## Features

- **Job Search**: Full-text search across title, company, and description
- **Smart Filtering**: Automatically excludes senior/advanced roles, focuses on junior to mid-level positions
- **Location Filter**: Filter jobs by geographic location
- **Sorting Options**: Sort by newest, oldest, relevance, or company name
- **Pagination**: Efficiently browse through all job listings
- **Auto-Cleanup**: Jobs older than 30 days are automatically removed
- **Job Details**: View full job info with similar job suggestions
- **Admin Panel**: Run manual scans (password protected)
- **Demo Mode**: Works without API keys using sample data
- **API Token Protection**: Secure endpoints for cron-triggered operations
- **Production Monitoring**: Built-in Prometheus metrics and Grafana dashboard support
- **Performance Tracking**: Real-time metrics for latency, traffic, errors, and saturation
- **Business Metrics**: Track job counts, scan success rates, and user activity

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Jinja2 Templates + TailwindCSS
- **Database**: SQLite (default) or PostgreSQL
- **Scheduler**: APScheduler
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

## Quick Start (Development)

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your API keys
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```
5. Open http://localhost:5000

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CSE_API_KEY` | No* | Google Custom Search API key |
| `GOOGLE_CSE_CX` | No* | Custom Search Engine ID |
| `ADMIN_PASSWORD` | **Yes (prod)** | Admin login password (default: admin123 - CHANGE THIS!) |
| `ADMIN_API_TOKEN` | **Yes (prod)** | Token for API authentication (cron jobs) |
| `SESSION_SECRET` | **Yes (prod)** | Session encryption key (auto-generates if missing but resets on restart) |

*App works in demo mode without these keys

> **Security Note**: In production, always set `ADMIN_PASSWORD`, `ADMIN_API_TOKEN`, and `SESSION_SECRET` to secure random values. Generate a session secret with: `python -c "import secrets; print(secrets.token_hex(32))"`

## Filtering Logic

### Excluded Keywords (Senior Roles)
- senior, sr, principal, architect, lead, manager, director, head, vp, staff, distinguished, chief

### Included Keywords (Junior/Mid Roles)
- analyst, associate, administrator, engineer, specialist, iam, identity, okta, entra, azure ad, sso, saml, oidc, scim, iga, pam, sailpoint, saviynt, ping, cyberark

### Experience Filters
- **Include**: 0-5, 1-3, 2-4, 3-5 years
- **Exclude**: 7+, 10+, 12+ years

## API Endpoints

### Public
- `GET /` - Main job board with search and filters
- `GET /job/{id}` - Individual job details
- `GET /login` - Admin login page
- `GET /api/jobs` - List jobs (JSON with search/filter params)
- `GET /api/stats` - Get statistics
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics endpoint

### Protected (Session Auth or API Token)
- `POST /admin/run-scan` - Trigger job scan
- `POST /admin/cleanup` - Remove jobs older than 30 days

### API Token Authentication
For cron jobs, use the `X-ADMIN-TOKEN` header:
```bash
curl -X POST https://your-app.com/admin/run-scan \
  -H "X-ADMIN-TOKEN: your_api_token"
```

---
Monitoring & Observability

IAM Job Scout includes **production-grade monitoring** with Prometheus metrics and Grafana dashboard support.

## 📊 Available Metrics

### Application Performance
- **HTTP Request Duration** - Response time histograms (p50, p95, p99)
- **Request Rate** - Requests per second by endpoint
- **Error Rate** - Failed requests and application errors
- **Concurrent Requests** - Active requests being processed

### Business Metrics
- **Total Jobs** - Current job count in database
- **New Jobs This Week** - Jobs added in last 7 days
- **Saved/Applied Jobs** - User engagement tracking
- **Scan Success Rate** - Job scan performance
- **Last Successful Scan** - Timestamp of last successful scan

### Database Performance
- **Query Duration** - Database query latency
- **Active Connections** - Connection pool utilization
- **Database Operations** - Operations by type (select, insert, update, delete)

### System Metrics
- **Uptime** - Application uptime in seconds
- **Memory Usage** - Process memory consumption
- **Python GC** - Garbage collection metrics

## 🚀 Quick Setup

### 1. Access Metrics Endpoint

```bash
curl http://your-app:5000/metrics
```

### 2. Configure Prometheus

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'iam-job-scout'
    static_configs:
      - targets: ['your-app-host:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 3. Create Grafana Dashboard

Import metrics and create panels for:
- Total Jobs (Stat)
- Request Rate (Time Series)
- Response Time p95 (Time Series)
- Error Rate % (Gauge)

## 📚 Detailed Documentation

- **[Quick Start Guide](docs/MONITORING_QUICKSTART.md)** - Get monitoring running in 10 minutes
- **[Complete Monitoring Guide](docs/MONITORING.md)** - Comprehensive documentation with examples
- **[Architecture Diagram](docs/ARCHITECTURE_DIAGRAM.md)** - Visual guide to monitoring setup
- **[Docker IP Guide](docs/DOCKER_IP_GUIDE.md)** - Networking tips for Docker deployments
- **[Prometheus Config Example](docs/prometheus.yml.example)** - Ready-to-use configuration
- **[Alert Rules Example](docs/prometheus-alerts.yml.example)** - Production-ready alerts

## 🎯 Key Monitoring Queries

```promql
# Total jobs in database
iam_jobs_total

# Request rate (req/sec)
rate(http_requests_total[5m])

# Error rate percentage
(sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# Response time 95th percentile
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Time since last successful scan (hours)
(time() - iam_last_successful_scan_timestamp) / 3600
```

## 🚨 Recommended Alerts

- Service Down (critical)
- Error Rate > 5% (warning)
- Response Time p95 > 2s (warning)
- No successful scan in 24 hours (warning)
- Database connections > 80% (warning)

---

# 
# Deployment



## Option A: Render (RECOMMENDED)

Render provides the easiest deployment experience with built-in cron job support.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/iam-job-scout.git
git push -u origin main
```

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: iam-job-scout
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Set Environment Variables

In the Render dashboard, go to "Environment" and add:
- `GOOGLE_CSE_API_KEY`
- `GOOGLE_CSE_CX`
- `ADMIN_PASSWORD`
- `ADMIN_API_TOKEN` (generate a secure random token)
- `SESSION_SECRET` (generate a secure random key)

### Step 4: Create Render Cron Job

1. Click "New +" → "Cron Job"
2. **Daily Scan Job**:
   - **Name**: iam-job-scout-scan
   - **Schedule**: `0 6 * * *` (6 AM daily)
   - **Command**:
     ```bash
     curl -X POST https://your-app.onrender.com/admin/run-scan \
       -H "X-ADMIN-TOKEN: $ADMIN_API_TOKEN" \
       -H "Accept: application/json"
     ```

---

## Option B: Fly.io (Docker)

Fly.io offers a generous free tier and easy Docker deployments.

### Step 1: Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

### Step 2: Launch the App

```bash
fly auth login
fly launch
```

When prompted:
- Choose a unique app name
- Select a region close to you
- Don't create a Postgres database (we use SQLite)
- Don't deploy yet

### Step 3: Set Secrets

```bash
fly secrets set GOOGLE_CSE_API_KEY="your_key"
fly secrets set GOOGLE_CSE_CX="your_cx"
fly secrets set ADMIN_PASSWORD="secure_password"
fly secrets set ADMIN_API_TOKEN="secure_token"
fly secrets set SESSION_SECRET="random_secret"
```

### Step 4: Deploy

```bash
fly deploy
```

### Step 5: Set Up Scheduled Jobs

Use GitHub Actions for scheduling:

Create `.github/workflows/scheduled-jobs.yml`:

```yaml
name: Scheduled Jobs

on:
  schedule:
    - cron: '0 6 * * *'  # Daily scan at 6 AM UTC

jobs:
  run-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Scan
        run: |
          curl -X POST https://your-app.fly.dev/admin/run-scan \
            -H "X-ADMIN-TOKEN: ${{ secrets.ADMIN_API_TOKEN }}" \
            -H "Accept: application/json"
```

---

## Option C: VPS (DigitalOcean / Lightsail / Ubuntu Server)

For full control over your deployment.

### Step 1: Provision a Server

- Create a small Ubuntu 22.04 VPS (1GB RAM is sufficient)
- DigitalOcean Droplet: $4-6/month
- AWS Lightsail: $3.50/month

### Step 2: Initial Server Setup

```bash
ssh root@your-server-ip

adduser deploy
usermod -aG sudo deploy

ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable

su - deploy
```

### Step 3: Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
exit
ssh deploy@your-server-ip
```

### Step 4: Deploy the Application

```bash
git clone https://github.com/yourusername/iam-job-scout.git
cd iam-job-scout

cp .env.example .env
nano .env  # Edit with your values

docker compose up -d
```

### Step 5: Set Up Caddy for HTTPS

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Edit `/etc/caddy/Caddyfile`:
```
yourdomain.com {
    reverse_proxy localhost:5000
}
```

```bash
sudo systemctl reload caddy
```

### Step 6: Set Up Cron Jobs

```bash
crontab -e
```

Add:
```
# Daily job scan at 6 AM
0 6 * * * curl -X POST http://localhost:5000/admin/run-scan -H "X-ADMIN-TOKEN: your_token" -H "Accept: application/json"
```

---

## HTTPS Guidance

- **Render**: HTTPS is automatic
- **Fly.io**: HTTPS is automatic
- **VPS with Caddy**: HTTPS is automatic (just point your domain to the server)

## Auto-Cleanup

Jobs older than 30 days are automatically removed when users visit the site. This keeps the job board fresh and relevant.

## Support

For issues or questions, please open a GitHub issue.
