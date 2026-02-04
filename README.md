# IAM & Cybersecurity Job Scout

A comprehensive web-based job board that helps entry to mid-level professionals find Identity & Access Management (IAM), Cybersecurity, and Cloud Security jobs across the USA. It aggregates job postings from multiple APIs and displays them in a clean, searchable interface with intelligent filtering.

## Features

- **Multi-API Job Aggregation**: Searches multiple job APIs concurrently (JSearch, Adzuna, RemoteOK)
- **Smart Filtering**: Automatically excludes senior/advanced roles, focuses on entry to mid-level positions
- **Comprehensive Coverage**:
  - IAM: Okta, SailPoint, CyberArk, Azure AD/Entra, Active Directory, PAM
  - Cybersecurity: SOC analyst, threat analyst, security operations, incident response, GRC
  - Cloud Security: AWS, Azure, GCP security roles, DevSecOps, cloud compliance
- **Intelligent Deduplication**: Fuzzy matching removes duplicate jobs from different sources
- **Full-text Search**: Search across job title, company, and description
- **Location Filter**: Filter jobs by geographic location across the US
- **Sorting Options**: Sort by newest, oldest, relevance, or company name
- **Job Status Tracking**: Mark jobs as saved, applied, or hidden
- **Auto-Cleanup**: Jobs older than 30 days are automatically removed
- **Scheduled Scans**: Automatic job searches on configurable days (Mon/Wed/Sat by default)
- **Admin Panel**: Run manual scans and manage jobs (password protected)
- **API Token Protection**: Secure endpoints for cron-triggered operations
- **Production Monitoring**: Built-in Prometheus metrics and Grafana dashboard support
- **Performance Tracking**: Real-time metrics for latency, traffic, errors, and saturation

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Frontend**: Jinja2 Templates + TailwindCSS
- **Database**: SQLite (default) or PostgreSQL
- **Scheduler**: APScheduler
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

---

## Running Your Own Instance

### Prerequisites

- **Python 3.11 or higher** - Check with `python --version`
- **pip** - Python package manager
- **Git** - For cloning the repository
- **Docker** (optional) - For containerized deployment

### Option 1: Local Development Setup

#### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/iam-job-scout.git
cd iam-job-scout
```

#### Step 2: Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Linux/macOS)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your preferred editor
nano .env  # or vim, code, etc.
```

See the [Environment Variables](#environment-variables) section below for details on each variable.

#### Step 5: Run the Application

```bash
python main.py
```

The application will start at **http://localhost:5000**

### Option 2: Docker Setup

#### Step 1: Clone and Configure

```bash
git clone https://github.com/yourusername/iam-job-scout.git
cd iam-job-scout
cp .env.example .env
nano .env  # Configure your environment variables
```

#### Step 2: Build and Run with Docker Compose

```bash
docker compose up -d
```

The application will be available at **http://localhost:5000**

#### Useful Docker Commands

```bash
# View logs
docker compose logs -f

# Stop the application
docker compose down

# Rebuild after changes
docker compose up -d --build

# View running containers
docker compose ps
```

---

## Environment Variables

### Job Search APIs

| Variable | Required | Description |
|----------|----------|-------------|
| `RAPIDAPI_KEY` | No* | JSearch API key from [RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) - searches Indeed, LinkedIn, Glassdoor |
| `ADZUNA_APP_ID` | No* | Adzuna API App ID from [developer.adzuna.com](https://developer.adzuna.com/) |
| `ADZUNA_APP_KEY` | No* | Adzuna API App Key (250 free requests/month) |

**Note**: RemoteOK API requires no authentication and is always enabled. The app works with any combination of APIs - configure whichever you have access to.

### Optional APIs

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CSE_API_KEY` | No | Google Custom Search API key (alternative search method) |
| `GOOGLE_CSE_CX` | No | Google Custom Search Engine ID |

### Security & Authentication

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_PASSWORD` | **Yes (prod)** | Admin login password. Default is `admin123` - **CHANGE THIS!** |
| `ADMIN_API_TOKEN` | **Yes (prod)** | Token for API authentication (used by cron jobs) |
| `SESSION_SECRET` | **Yes (prod)** | Session encryption key. Auto-generates if missing but resets on restart |

### Database

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | PostgreSQL connection string. Defaults to SQLite if not set |

**Example PostgreSQL URL**: `postgresql://user:password@host:port/dbname`

### Scheduler (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `SCAN_DAYS` | No | Days to run scans (default: `0,2,5` = Mon/Wed/Sat) |
| `SCAN_HOUR` | No | Hour to run scans in UTC (default: `6`) |

### Security Best Practices

For production deployments, generate secure values:

```bash
# Generate a secure session secret
python -c "import secrets; print(secrets.token_hex(32))"

# Generate a secure admin password
python -c "import secrets; print(secrets.token_urlsafe(16))"

# Generate an API token
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Getting API Keys

### JSearch (RapidAPI) - Recommended

1. Go to [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
2. Sign up for a free account
3. Subscribe to the JSearch API (free tier available)
4. Copy your API key from the dashboard
5. Set `RAPIDAPI_KEY=your_key` in `.env`

### Adzuna

1. Go to [Adzuna Developer Portal](https://developer.adzuna.com/)
2. Sign up and create an application
3. Get your App ID and App Key
4. Set both in `.env`:
   ```
   ADZUNA_APP_ID=your_app_id
   ADZUNA_APP_KEY=your_app_key
   ```

### RemoteOK

No configuration needed - this API is always available without authentication.

---

## Filtering Logic

### Excluded Keywords (Senior Roles)
- senior, sr, principal, architect, lead, manager, director, head, vp, staff, distinguished, chief

### Included Keywords (Junior/Mid Roles)
- analyst, associate, administrator, engineer, specialist, iam, identity, okta, entra, azure ad, sso, saml, oidc, scim, iga, pam, sailpoint, saviynt, ping, cyberark

### Experience Filters
- **Include**: 0-5, 1-3, 2-4, 3-5 years
- **Exclude**: 7+, 10+, 12+ years

---

## API Endpoints

### Public
- `GET /` - Main job board with search and filters
- `GET /job/{id}` - Individual job details
- `GET /saved` - Saved and applied jobs (requires login)
- `GET /login` - Admin login page
- `GET /api/jobs` - List jobs (JSON with search/filter params)
- `GET /api/stats` - Get statistics
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics endpoint

### Protected (Session Auth or API Token)
- `POST /admin/run-scan` - Trigger job scan
- `POST /admin/cleanup` - Remove jobs older than 30 days
- `POST /job/{id}/status` - Update job status (saved/applied/hidden)
- `POST /job/{id}/notes` - Add notes to a job

### API Token Authentication
For cron jobs or external integrations, use the `X-ADMIN-TOKEN` header:
```bash
curl -X POST https://your-app.com/admin/run-scan \
  -H "X-ADMIN-TOKEN: your_api_token" \
  -H "Accept: application/json"
```

---

## Monitoring & Observability

IAM Job Scout includes **production-grade monitoring** with Prometheus metrics and Grafana dashboard support.

### Available Metrics

#### Application Performance
- **HTTP Request Duration** - Response time histograms (p50, p95, p99)
- **Request Rate** - Requests per second by endpoint
- **Error Rate** - Failed requests and application errors
- **Concurrent Requests** - Active requests being processed

#### Business Metrics
- **Total Jobs** - Current job count in database
- **New Jobs This Week** - Jobs added in last 7 days
- **Saved/Applied Jobs** - User engagement tracking
- **Scan Success Rate** - Job scan performance
- **Last Successful Scan** - Timestamp of last successful scan

#### Database Performance
- **Query Duration** - Database query latency
- **Active Connections** - Connection pool utilization
- **Database Operations** - Operations by type (select, insert, update, delete)

### Quick Monitoring Setup

#### 1. Access Metrics Endpoint

```bash
curl http://localhost:5000/metrics
```

#### 2. Configure Prometheus

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'iam-job-scout'
    static_configs:
      - targets: ['your-app-host:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Detailed Documentation

- **[Quick Start Guide](docs/MONITORING_QUICKSTART.md)** - Get monitoring running in 10 minutes
- **[Complete Monitoring Guide](docs/MONITORING.md)** - Comprehensive documentation with examples
- **[Architecture Diagram](docs/ARCHITECTURE_DIAGRAM.md)** - Visual guide to system architecture
- **[Docker IP Guide](docs/DOCKER_IP_GUIDE.md)** - Networking tips for Docker deployments
- **[Prometheus Config Example](docs/prometheus.yml.example)** - Ready-to-use configuration
- **[Alert Rules Example](docs/prometheus-alerts.yml.example)** - Production-ready alerts

### Key Monitoring Queries

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

---

## Production Deployment

### Option A: Render (Recommended)

Render provides the easiest deployment experience with built-in cron job support.

#### Step 1: Push to GitHub

```bash
git remote add origin https://github.com/yourusername/iam-job-scout.git
git push -u origin main
```

#### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: iam-job-scout
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Step 3: Set Environment Variables

In the Render dashboard, go to "Environment" and add:
- `RAPIDAPI_KEY` (if using JSearch)
- `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` (if using Adzuna)
- `ADMIN_PASSWORD` (use a strong password!)
- `ADMIN_API_TOKEN` (generate a secure random token)
- `SESSION_SECRET` (generate a secure random key)

#### Step 4: Create Render Cron Job

1. Click "New +" → "Cron Job"
2. **Daily Scan Job**:
   - **Name**: iam-job-scout-scan
   - **Schedule**: `0 6 * * 1,3,6` (6 AM Mon/Wed/Sat)
   - **Command**:
     ```bash
     curl -X POST https://your-app.onrender.com/admin/run-scan \
       -H "X-ADMIN-TOKEN: $ADMIN_API_TOKEN" \
       -H "Accept: application/json"
     ```

---

### Option B: Fly.io (Docker)

Fly.io offers a generous free tier and easy Docker deployments.

#### Step 1: Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

#### Step 2: Launch the App

```bash
fly auth login
fly launch
```

When prompted:
- Choose a unique app name
- Select a region close to you
- Don't create a Postgres database (we use SQLite)
- Don't deploy yet

#### Step 3: Set Secrets

```bash
fly secrets set RAPIDAPI_KEY="your_key"
fly secrets set ADZUNA_APP_ID="your_app_id"
fly secrets set ADZUNA_APP_KEY="your_app_key"
fly secrets set ADMIN_PASSWORD="secure_password"
fly secrets set ADMIN_API_TOKEN="secure_token"
fly secrets set SESSION_SECRET="random_secret"
```

#### Step 4: Deploy

```bash
fly deploy
```

#### Step 5: Set Up Scheduled Jobs

Use GitHub Actions for scheduling. Create `.github/workflows/scheduled-jobs.yml`:

```yaml
name: Scheduled Jobs

on:
  schedule:
    - cron: '0 6 * * 1,3,6'  # 6 AM Mon/Wed/Sat

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

### Option C: VPS (DigitalOcean / Lightsail / Ubuntu Server)

For full control over your deployment.

#### Step 1: Provision a Server

- Create a small Ubuntu 22.04 VPS (1GB RAM is sufficient)
- DigitalOcean Droplet: $4-6/month
- AWS Lightsail: $3.50/month

#### Step 2: Initial Server Setup

```bash
ssh root@your-server-ip

# Create deploy user
adduser deploy
usermod -aG sudo deploy

# Configure firewall
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable

# Switch to deploy user
su - deploy
```

#### Step 3: Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
exit
ssh deploy@your-server-ip
```

#### Step 4: Deploy the Application

```bash
git clone https://github.com/yourusername/iam-job-scout.git
cd iam-job-scout

# Configure environment
cp .env.example .env
nano .env  # Edit with your values

# Start the application
docker compose up -d
```

#### Step 5: Set Up Caddy for HTTPS

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

#### Step 6: Set Up Cron Jobs

```bash
crontab -e
```

Add:
```
# Job scan at 6 AM on Mon/Wed/Sat
0 6 * * 1,3,6 curl -X POST http://localhost:5000/admin/run-scan -H "X-ADMIN-TOKEN: your_token" -H "Accept: application/json"
```

---

## Project Structure

```
iam-job-scout/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
├── Dockerfile              # Docker containerization
├── docker-compose.yml      # Docker Compose orchestration
├── .env.example            # Environment variable template
│
├── db/                     # Database layer
│   ├── database.py         # SQLAlchemy setup
│   └── models.py           # ORM models (Job, ScanRun, Settings)
│
├── jobs/                   # Job service layer
│   └── job_service.py      # Business logic for job management
│
├── search/                 # Multi-API job search
│   ├── api_manager.py      # API orchestration
│   ├── jsearch.py          # JSearch API (RapidAPI)
│   ├── adzuna.py           # Adzuna API
│   ├── remoteok.py         # RemoteOK API (no auth)
│   ├── filters.py          # Job filtering logic
│   └── deduplication.py    # Fuzzy duplicate detection
│
├── scheduler/              # Job scheduling
│   └── scheduler_service.py
│
├── monitoring/             # Prometheus metrics
│   ├── metrics.py          # Metric definitions
│   ├── middleware.py       # HTTP instrumentation
│   └── db_metrics.py       # Database instrumentation
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── job_detail.html
│   ├── login.html
│   └── saved_jobs.html
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── MONITORING.md
│   └── ...
│
└── tests/                  # Test suite
    └── test_imports.py
```

---

## Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with verbose output
pytest -v
```

---

## Troubleshooting

### Common Issues

**App starts but no jobs appear**
- Check if API keys are configured in `.env`
- Run a manual scan via the admin panel or API
- Check logs for API errors

**"Internal Server Error" on scan**
- Verify API keys are valid and have available quota
- Check the application logs for detailed error messages

**Database errors**
- For SQLite: Ensure write permissions in the app directory
- For PostgreSQL: Verify the `DATABASE_URL` connection string

**Jobs not updating automatically**
- Check if the scheduler is running (logs will show "Scheduler started")
- Verify cron job configuration if using external scheduling

### Getting Help

For issues or questions, please [open a GitHub issue](https://github.com/yourusername/iam-job-scout/issues).

---

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
