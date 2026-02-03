# IAM Job Scout - Architecture Guide

This document describes the system architecture and provides diagrams you can use or recreate.

## System Overview

IAM Job Scout is a multi-API job aggregation platform built with FastAPI. It searches multiple job APIs, deduplicates results, and presents them through a web dashboard.

---

## Complete System Architecture (Single View)

**Copy this Mermaid code into your README.md - GitHub will render it automatically:**

```mermaid
flowchart TB
    subgraph USER["👤 USER LAYER"]
        Browser["🌐 Web Browser"]
        Admin["👨‍💼 Admin User"]
        Cron["⏰ Scheduled Cron"]
    end

    subgraph FRONTEND["🎨 FRONTEND (templates/)"]
        Dashboard["dashboard.html<br/>• Job listings<br/>• Search & filters<br/>• API status"]
        JobDetail["job_detail.html<br/>• Full job info<br/>• Similar jobs"]
        SavedJobs["saved_jobs.html<br/>• Saved jobs<br/>• Applied jobs"]
        Login["login.html<br/>• Admin auth"]
    end

    subgraph WEBAPP["⚡ WEB APPLICATION (main.py)"]
        FastAPI["FastAPI App<br/>Port 5000"]
        Routes["Routes<br/>• GET /<br/>• GET /job/{id}<br/>• POST /admin/run-scan<br/>• GET /api/jobs"]
        Middleware["Middleware<br/>• Session<br/>• Prometheus"]
        Static["Static Files<br/>• CSS<br/>• JavaScript"]
    end

    subgraph SERVICES["🔧 SERVICES"]
        JobService["JobService<br/>(jobs/job_service.py)<br/>• run_scan()<br/>• search_jobs()<br/>• update_status()"]
        Scheduler["SchedulerService<br/>(scheduler/)<br/>• APScheduler<br/>• Mon/Wed/Sat 6AM UTC"]
    end

    subgraph SEARCH["🔍 SEARCH LAYER (search/)"]
        APIManager["APIManager<br/>(api_manager.py)<br/>• Orchestrates APIs<br/>• Concurrent calls"]

        subgraph APIs["Job Search APIs"]
            JSearch["JSearchAPI<br/>• 18 queries<br/>• RapidAPI"]
            Adzuna["AdzunaAPI<br/>• 14 queries<br/>• 250/month free"]
            RemoteOK["RemoteOKAPI<br/>• 1 query<br/>• No auth needed"]
        end

        Dedup["JobDeduplicator<br/>(deduplication.py)<br/>• Fuzzy matching<br/>• 85% title threshold"]
        Filter["JobFilter<br/>(filters.py)<br/>• Junior/Mid filter<br/>• Score calculation"]
    end

    subgraph DATA["💾 DATA LAYER (db/)"]
        ORM["SQLAlchemy ORM<br/>(database.py)"]
        subgraph Tables["Database Tables"]
            Jobs["Jobs Table<br/>• title, company<br/>• location, url<br/>• score, status"]
            ScanRun["ScanRun Table<br/>• started_at<br/>• jobs_found<br/>• status"]
        end
        DB[(SQLite/PostgreSQL)]
    end

    subgraph EXTERNAL["🌍 EXTERNAL SERVICES"]
        JSearchExt["JSearch API<br/>(RapidAPI)<br/>Indeed, LinkedIn,<br/>Glassdoor"]
        AdzunaExt["Adzuna API<br/>US Job Market<br/>250 req/month"]
        RemoteOKExt["RemoteOK API<br/>Remote Jobs Only<br/>Free, No Auth"]
    end

    subgraph MONITORING["📊 MONITORING (monitoring/)"]
        Metrics["Prometheus Metrics<br/>• Request latency<br/>• Scan duration<br/>• Job counts"]
        Prometheus["Prometheus Server<br/>:9090"]
        Grafana["Grafana<br/>:3000<br/>Dashboards"]
    end

    %% User connections
    Browser --> FastAPI
    Admin --> FastAPI
    Cron --> Scheduler

    %% Frontend connections
    FastAPI --> Dashboard
    FastAPI --> JobDetail
    FastAPI --> SavedJobs
    FastAPI --> Login
    FastAPI --> Static

    %% Service connections
    Routes --> JobService
    Scheduler --> JobService
    Middleware --> Metrics

    %% Search flow
    JobService --> APIManager
    APIManager --> JSearch
    APIManager --> Adzuna
    APIManager --> RemoteOK

    JSearch --> JSearchExt
    Adzuna --> AdzunaExt
    RemoteOK --> RemoteOKExt

    JSearch --> Filter
    Adzuna --> Filter
    RemoteOK --> Filter
    Filter --> Dedup

    %% Data flow
    JobService --> ORM
    ORM --> Jobs
    ORM --> ScanRun
    Jobs --> DB
    ScanRun --> DB

    %% Monitoring flow
    Metrics --> Prometheus
    Prometheus --> Grafana

    %% Styling
    classDef userStyle fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef frontendStyle fill:#10B981,stroke:#065F46,color:#fff
    classDef webappStyle fill:#8B5CF6,stroke:#5B21B6,color:#fff
    classDef serviceStyle fill:#F59E0B,stroke:#92400E,color:#fff
    classDef searchStyle fill:#EC4899,stroke:#9D174D,color:#fff
    classDef dataStyle fill:#06B6D4,stroke:#0E7490,color:#fff
    classDef externalStyle fill:#6B7280,stroke:#374151,color:#fff
    classDef monitorStyle fill:#EF4444,stroke:#B91C1C,color:#fff

    class Browser,Admin,Cron userStyle
    class Dashboard,JobDetail,SavedJobs,Login frontendStyle
    class FastAPI,Routes,Middleware,Static webappStyle
    class JobService,Scheduler serviceStyle
    class APIManager,JSearch,Adzuna,RemoteOK,Dedup,Filter searchStyle
    class ORM,Jobs,ScanRun,DB dataStyle
    class JSearchExt,AdzunaExt,RemoteOKExt externalStyle
    class Metrics,Prometheus,Grafana monitorStyle
```

## Component Diagram (Mermaid)

```mermaid
graph LR
    subgraph Frontend
        A[Dashboard] --> B[Job Detail]
        A --> C[Saved Jobs]
        A --> D[Login]
    end

    subgraph Backend
        E[FastAPI Routes]
        F[Job Service]
        G[API Manager]
    end

    subgraph APIs
        H[JSearch]
        I[Adzuna]
        J[RemoteOK]
    end

    subgraph Database
        K[(Jobs Table)]
        L[(ScanRun Table)]
    end

    Frontend --> E
    E --> F
    F --> G
    G --> H & I & J
    F --> K & L
```

## Data Flow Diagram (Mermaid)

```mermaid
sequenceDiagram
    participant U as User/Scheduler
    participant F as FastAPI
    participant JS as JobService
    participant AM as APIManager
    participant APIs as External APIs
    participant DB as Database

    U->>F: Trigger Scan
    F->>JS: run_scan()
    JS->>AM: search_all()

    par Concurrent API Calls
        AM->>APIs: JSearch queries
        AM->>APIs: Adzuna queries
        AM->>APIs: RemoteOK query
    end

    APIs-->>AM: Job results
    AM->>AM: Deduplicate jobs
    AM-->>JS: Aggregated jobs
    JS->>DB: Store new jobs
    JS-->>F: Scan results
    F-->>U: Success response
```

## ASCII Diagram

For environments that don't support Mermaid:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│                           ┌─────────────┐                               │
│                           │ Web Browser │                               │
│                           └──────┬──────┘                               │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼──────────────────────────────────────┐
│                              WEB LAYER                                   │
│  ┌─────────────┐  ┌─────────────┴─────────────┐  ┌─────────────────┐   │
│  │   Static    │  │     FastAPI Application    │  │   Prometheus    │   │
│  │  (CSS/JS)   │  │  ┌─────────────────────┐  │  │    Metrics      │   │
│  └─────────────┘  │  │  Jinja2 Templates   │  │  └─────────────────┘   │
│                   │  └─────────────────────┘  │                         │
│                   └─────────────┬─────────────┘                         │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                           SERVICE LAYER                                  │
│       ┌─────────────────────────┴─────────────────────────┐             │
│       │                    JobService                      │             │
│       └─────────────────────────┬─────────────────────────┘             │
│                                 │                                        │
│       ┌─────────────────────────┴─────────────────────────┐             │
│       │              SchedulerService (APScheduler)        │             │
│       │           (Mon/Wed/Sat @ 6:00 AM UTC)             │             │
│       └───────────────────────────────────────────────────┘             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                           SEARCH LAYER                                   │
│                   ┌─────────────┴─────────────┐                         │
│                   │        APIManager          │                         │
│                   └─────────────┬─────────────┘                         │
│         ┌───────────────────────┼───────────────────────┐               │
│         │                       │                       │               │
│  ┌──────┴──────┐  ┌─────────────┴───────────┐  ┌───────┴───────┐       │
│  │  JSearchAPI │  │       AdzunaAPI         │  │  RemoteOKAPI  │       │
│  │  (18 queries)│  │      (14 queries)       │  │  (1 query)    │       │
│  └──────┬──────┘  └─────────────┬───────────┘  └───────┬───────┘       │
│         │                       │                       │               │
│         └───────────────────────┼───────────────────────┘               │
│                   ┌─────────────┴─────────────┐                         │
│                   │     JobDeduplicator       │                         │
│                   │   (Fuzzy matching)        │                         │
│                   └───────────────────────────┘                         │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                            DATA LAYER                                    │
│                   ┌─────────────┴─────────────┐                         │
│                   │     SQLAlchemy ORM        │                         │
│                   └─────────────┬─────────────┘                         │
│                   ┌─────────────┴─────────────┐                         │
│                   │  ┌─────┐ ┌───────┐ ┌────┐ │                         │
│                   │  │Jobs │ │ScanRun│ │... │ │                         │
│                   │  └─────┘ └───────┘ └────┘ │                         │
│                   │    SQLite / PostgreSQL    │                         │
│                   └───────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                         EXTERNAL SERVICES                                │
│    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │
│    │    JSearch     │  │     Adzuna     │  │    RemoteOK    │          │
│    │   (RapidAPI)   │  │   (Free Tier)  │  │   (Free API)   │          │
│    │ Indeed,LinkedIn│  │  250 req/month │  │  No Auth Req   │          │
│    └────────────────┘  └────────────────┘  └────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
iam-job-scout/
├── main.py                 # FastAPI application entry point
├── db/
│   ├── database.py         # SQLAlchemy setup
│   └── models.py           # ORM models (Job, ScanRun, Settings)
├── jobs/
│   └── job_service.py      # Business logic for jobs
├── search/
│   ├── api_manager.py      # Orchestrates all APIs
│   ├── jsearch.py          # JSearch/RapidAPI integration
│   ├── adzuna.py           # Adzuna API integration
│   ├── remoteok.py         # RemoteOK API integration
│   ├── deduplication.py    # Fuzzy duplicate detection
│   └── filters.py          # Job filtering logic
├── scheduler/
│   └── scheduler_service.py # APScheduler setup
├── monitoring/
│   ├── metrics.py          # Prometheus metrics
│   └── db_metrics.py       # Database metrics
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, images
└── tests/                  # Pytest test suite
```

## Tools to Create Diagrams

### 1. draw.io (Recommended - Free)
- Website: https://draw.io or https://app.diagrams.net
- Export as PNG/SVG for README
- Can import from Mermaid

### 2. Lucidchart
- Website: https://lucidchart.com
- Professional diagrams
- Free tier available

### 3. Excalidraw (Hand-drawn style)
- Website: https://excalidraw.com
- Creates informal, sketch-like diagrams
- Great for presentations

### 4. Mermaid Live Editor
- Website: https://mermaid.live
- Paste the Mermaid code above
- Export as PNG/SVG

### 5. PlantUML
- Website: https://plantuml.com
- Text-based diagrams
- Good for sequence diagrams

## Color Scheme Suggestions

For a professional look, use these colors:

| Component | Color | Hex Code |
|-----------|-------|----------|
| Client/UI | Blue | #3B82F6 |
| API Layer | Green | #10B981 |
| Services | Purple | #8B5CF6 |
| Database | Orange | #F59E0B |
| External APIs | Gray | #6B7280 |
| Monitoring | Red | #EF4444 |

## Key Architectural Decisions

1. **Multi-API Strategy**: Uses 3 job APIs to maximize coverage and reduce single-point-of-failure risk

2. **Async Processing**: All API calls are async with concurrent execution for performance

3. **Fuzzy Deduplication**: Uses SequenceMatcher for ~85% title and ~80% company similarity matching

4. **Rate Limiting**: Built-in delays between API calls to respect rate limits

5. **Caching**: In-memory caching for stats and locations (5-minute TTL)

6. **Scheduled Scans**: APScheduler runs scans on configurable days/times

7. **Monitoring**: Prometheus metrics for observability

## API Flow Summary

```
User Request → FastAPI → JobService → APIManager
                                          ↓
                              ┌───────────┼───────────┐
                              ↓           ↓           ↓
                          JSearch     Adzuna     RemoteOK
                              ↓           ↓           ↓
                              └───────────┼───────────┘
                                          ↓
                                   Deduplicate
                                          ↓
                                   Filter Jobs
                                          ↓
                                   Store in DB
                                          ↓
                                   Return Results
```
