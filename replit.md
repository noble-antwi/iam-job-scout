# IAM Job Scout

## Overview
IAM Job Scout is a web-based job board that helps junior to mid-level professionals find Identity & Access Management (IAM) jobs across the USA. It automatically searches for job postings from Indeed, LinkedIn, Glassdoor, and other sources using the JSearch API and displays them in a clean, searchable interface.

## Current State
- **Status**: Production ready with real job data
- **Framework**: Python + FastAPI with Jinja2 templates
- **Database**: PostgreSQL (Replit-provided)
- **Job Source**: JSearch API (aggregates from Indeed, LinkedIn, Glassdoor, ZipRecruiter, etc.)
- **Scanning Schedule**: Monday, Wednesday, Saturday at 6:00 AM UTC

---

## How the API Works

### JSearch API (RapidAPI)
The app uses the JSearch API from RapidAPI to find jobs. Here's how it works:

#### What counts as a "request"?
- **Each API call = 1 request** (not each job found)
- If one search returns 50 jobs, that's still just **1 request**
- Your free tier allows **200 requests/month**

#### How we use the requests
| Component | Details |
|-----------|---------|
| Queries per scan | 10 different IAM-related searches |
| Scans per week | 3 (Monday, Wednesday, Saturday) |
| Scans per month | ~12-13 |
| **Total requests/month** | **~120-130** |
| Buffer remaining | ~70-80 requests |

This gives you good coverage while staying safely under your 200/month limit.

### Search Queries We Use
Each scan runs these 10 searches to find a variety of IAM jobs:

1. `IAM analyst entry level USA`
2. `Identity access management engineer junior USA`
3. `Okta administrator USA`
4. `Azure AD specialist USA`
5. `SailPoint engineer USA`
6. `Identity management analyst USA`
7. `SSO specialist entry level USA`
8. `CyberArk administrator junior USA`
9. `IAM security analyst USA`
10. `Access management engineer USA`

### Filtering Logic
Jobs are automatically filtered to show only junior/mid-level positions:

**Excludes (senior roles):**
- senior, principal, architect, lead, manager, director, head, vp, staff, chief, executive

**Includes (junior/mid roles):**
- analyst, associate, administrator, engineer, specialist, iam, identity, okta, azure, sailpoint, cyberark

**Experience requirements:**
- Keeps: 0-5 years experience
- Filters out: 7+ years experience requirements

---

## Project Architecture

### Directory Structure
```
/
├── main.py                   # FastAPI application entry point
├── db/                       # Database layer
│   ├── database.py           # SQLAlchemy configuration
│   └── models.py             # Database models (Job, Settings, ScanRun)
├── search/                   # Job search functionality
│   ├── jsearch.py            # JSearch API client (RapidAPI)
│   └── filters.py            # Junior/mid role filtering logic
├── jobs/                     # Job service layer
│   └── job_service.py        # Job CRUD, search, and cleanup
├── scheduler/                # APScheduler configuration
│   └── scheduler_service.py  # Scheduled scans + daily cleanup
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base template with TailwindCSS
│   ├── dashboard.html        # Main job board page
│   ├── job_detail.html       # Individual job view
│   └── login.html            # Admin login page
├── static/                   # Static files (CSS, images)
├── requirements.txt          # Python dependencies
└── replit.md                 # This documentation file
```

### Key Components

#### 1. Job Search (`search/jsearch.py`)
- Connects to RapidAPI's JSearch API
- Runs 10 targeted IAM job searches
- Parses and normalizes job data
- Falls back to demo data if API key not configured

#### 2. Job Filtering (`search/filters.py`)
- Filters out senior-level positions
- Scores jobs based on relevance (higher = better match for junior/mid roles)
- Checks experience requirements in job descriptions

#### 3. Job Service (`jobs/job_service.py`)
- Manages database operations (CRUD)
- Handles job search with filters
- Deduplicates jobs by URL
- Provides statistics and similar job suggestions

#### 4. Scheduler (`scheduler/scheduler_service.py`)
- Runs job scans on Monday, Wednesday, Saturday at 6:00 AM UTC
- Runs cleanup daily at 3:00 AM UTC (removes jobs older than 30 days)
- Uses APScheduler with AsyncIO

---

## Features

### For Job Seekers
1. **Job Search**: Full-text search across job title, company, and description
2. **Location Filter**: Filter jobs by city, state, or "Remote"
3. **Sorting Options**: 
   - Newest First (default)
   - Oldest First
   - By Relevance Score
   - By Company Name
4. **Pagination**: Browse through all jobs, 20 per page
5. **Job Details**: View full job info with direct apply link
6. **Similar Jobs**: See related positions on job detail pages

### For Admins
1. **Manual Scan**: Trigger a job scan immediately (login required)
2. **Manual Cleanup**: Remove old jobs manually
3. **Password Protection**: Admin features require login

### Automatic Features
1. **Scheduled Scans**: 3x per week (Mon/Wed/Sat at 6 AM UTC)
2. **Auto-Cleanup**: Jobs older than 30 days removed daily at 3 AM UTC
3. **Deduplication**: Same job URL won't be added twice

---

## Environment Variables

### Required
| Variable | Description | Example |
|----------|-------------|---------|
| `RAPIDAPI_KEY` | Your RapidAPI key for JSearch | `aee7e21e4d...` |

### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_PASSWORD` | Password for admin login | `admin123` |
| `ADMIN_API_TOKEN` | Token for API-based admin actions | (none) |
| `SESSION_SECRET` | Session encryption key | Auto-generated |
| `SCAN_DAYS` | Days to run scans | `mon,wed,sat` |
| `SCAN_HOUR` | Hour to run scans (UTC) | `6` |

---

## API Endpoints

### Public Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard with job listings |
| GET | `/job/{id}` | Individual job details |
| GET | `/login` | Admin login page |
| GET | `/logout` | Logout admin |
| GET | `/health` | Health check endpoint |

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | Get jobs as JSON (supports search params) |
| GET | `/api/stats` | Get job statistics |

### Admin Endpoints (require login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/run-scan` | Trigger immediate job scan |
| POST | `/admin/cleanup` | Remove jobs older than 30 days |

---

## Request Budget Planning

### Free Tier (200 requests/month)
| Frequency | Requests/Month | Status |
|-----------|----------------|--------|
| 3x/week (current) | ~120 | Safe |
| 4x/week | ~160 | Tight |
| Daily | ~300 | Over limit |
| Hourly | ~7,200 | Way over |

### If You Need More Requests
- **Basic Plan**: ~$10/month for 10,000 requests
- **Pro Plan**: Higher limits available on RapidAPI

---

## Job Sources (via JSearch)
The JSearch API aggregates jobs from multiple sources:
- Indeed
- LinkedIn
- Glassdoor
- ZipRecruiter
- Monster
- SimplyHired
- Company career pages
- And more...

---

## Database Schema

### Jobs Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String | Job title |
| company | String | Company name |
| location | String | Job location |
| snippet | Text | Job description snippet |
| url | String | Apply link (unique) |
| source | String | Where job was found |
| score | Float | Relevance score |
| is_new | Boolean | Flag for new jobs |
| created_at | DateTime | When added to database |

### ScanRun Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| started_at | DateTime | Scan start time |
| completed_at | DateTime | Scan completion time |
| jobs_found | Integer | Total jobs from API |
| new_jobs | Integer | New jobs added |
| status | String | running/completed/failed |
| error_message | Text | Error details if failed |

---

## Running the App

### Development
```bash
python main.py
```
The app runs on port 5000 with hot reload enabled.

### Admin Access
1. Go to `/login`
2. Enter password (default: `admin123`)
3. Once logged in, you'll see "Run Scan" button on dashboard

### Manual API Scan
```bash
curl -X POST http://localhost:5000/admin/run-scan \
  -H "Accept: application/json"
```

---

## How to Host/Publish This Website

### On Replit (Recommended)

Publishing on Replit makes your app available to anyone on the internet with a public URL.

#### Step 1: Prepare for Production
Before publishing, make sure:
- [x] `RAPIDAPI_KEY` is set in Secrets
- [x] Change `ADMIN_PASSWORD` to something secure (optional but recommended)

#### Step 2: Publish the App
1. Click the **"Publish"** button in the top-right corner of Replit
2. Choose **"Autoscale"** deployment type (recommended for web apps)
3. Set the run command: `python main.py`
4. Configure resources (1 vCPU / 2GB RAM is usually enough)
5. Click **"Publish"**

#### Step 3: Access Your Live Site
After publishing, you'll get a URL like: `https://your-app-name.replit.app`

#### Costs
| Traffic Level | Estimated Cost |
|--------------|----------------|
| Low (few visitors/day) | ~$1-2/month |
| Moderate (hundreds/day) | ~$5-15/month |
| High (thousands/day) | ~$20+/month |

Costs are deducted from your monthly credits first (Core plan = $25/month in credits).

### Hosting on Your Laptop or Ubuntu Server

You can run this app locally on your own computer or server.

#### Requirements
- Python 3.11+
- PostgreSQL database (local or cloud)
- Git (to clone the code)

#### Step-by-Step for Ubuntu/Linux

```bash
# 1. Install Python and PostgreSQL
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql postgresql-contrib

# 2. Start PostgreSQL and create database
sudo systemctl start postgresql
sudo -u postgres createdb iamjobscout
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'yourpassword';"

# 3. Clone or copy the project files
git clone <your-repo-url> iamjobscout
cd iamjobscout

# 4. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Set environment variables
export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/iamjobscout"
export RAPIDAPI_KEY="your_rapidapi_key"
export ADMIN_PASSWORD="your_secure_password"

# 7. Run the app
python main.py
```

The app will be available at `http://localhost:5000`

#### Step-by-Step for Windows

```powershell
# 1. Install Python 3.11 from python.org
# 2. Install PostgreSQL from postgresql.org

# 3. Open PowerShell and navigate to project folder
cd C:\path\to\iamjobscout

# 4. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Set environment variables
$env:DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5432/iamjobscout"
$env:RAPIDAPI_KEY = "your_rapidapi_key"
$env:ADMIN_PASSWORD = "your_secure_password"

# 7. Run the app
python main.py
```

#### Running as a Background Service (Ubuntu)

To keep the app running after you close the terminal:

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/iamjobscout.service
```

Add this content:
```ini
[Unit]
Description=IAM Job Scout
After=network.target postgresql.service

[Service]
User=your_username
WorkingDirectory=/path/to/iamjobscout
Environment="DATABASE_URL=postgresql://postgres:password@localhost:5432/iamjobscout"
Environment="RAPIDAPI_KEY=your_key"
Environment="ADMIN_PASSWORD=your_password"
ExecStart=/path/to/iamjobscout/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable iamjobscout
sudo systemctl start iamjobscout
```

### Hosting on Cloud Platforms

#### Platform-Specific Guides
- **Railway**: Connect GitHub repo, add PostgreSQL plugin, set env vars
- **Render**: Create web service, add PostgreSQL, set env vars
- **DigitalOcean App Platform**: Similar to above
- **AWS/GCP/Azure**: Use container deployment with Docker

---

## Recent Changes
- **2024-12-19**: Changed to 3x weekly scans (Mon/Wed/Sat) to maximize free tier usage
- **2024-12-19**: Added comprehensive documentation
- **2024-12-18**: Switched from Google CSE to JSearch API
- **2024-12-18**: Added automatic scheduled job scanning
- **2024-12-18**: Added search, filtering, pagination, and sorting
- **2024-12-18**: Added job detail pages with similar jobs
- **2024-12-18**: Added auto-cleanup for jobs older than 30 days

---

## Troubleshooting

### No jobs appearing?
1. Check if `RAPIDAPI_KEY` is set in Secrets
2. Try running a manual scan from the admin panel
3. Check the console logs for API errors

### API quota exceeded?
1. Wait until next month for quota reset
2. Or upgrade to a paid plan on RapidAPI

### Jobs not filtering correctly?
- The filter is intentionally permissive to not miss opportunities
- Senior jobs occasionally slip through if titles are ambiguous
- Adjust filters in `search/filters.py` if needed

---

## User Preferences
- Simple Jinja2 templates with TailwindCSS
- No email notifications - all jobs displayed on web
- Auto-cleanup of old jobs (30 days)
- 3x weekly automatic scanning
