import os
import secrets
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, Form, Header, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from db.database import engine, Base, get_db, SessionLocal
from db.models import Job, Settings, ScanRun
from jobs.job_service import JobService
from scheduler.scheduler_service import SchedulerService
from prometheus_fastapi_instrumentator import Instrumentator

# Import new monitoring module
from monitoring import (
    PrometheusMiddleware,
    SCAN_RUNS_TOTAL,
    SCAN_DURATION,
    SCAN_ERRORS,
    JOB_STATUS_UPDATES,
    LAST_SUCCESSFUL_SCAN_TIMESTAMP,
    update_business_metrics,
    initialize_metrics,
)
from monitoring.db_metrics import update_connection_pool_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN", "")
SCAN_DAYS = os.getenv("SCAN_DAYS", "mon,wed,sat")
SCAN_HOUR = int(os.getenv("SCAN_HOUR", "6"))

_session_secret = os.getenv("SESSION_SECRET", "")
if not _session_secret:
    _session_secret = secrets.token_hex(32)
    logger.warning("SESSION_SECRET not set. Using auto-generated secret (sessions will reset on restart).")
SESSION_SECRET = _session_secret

if ADMIN_PASSWORD == "admin123":
    logger.warning("Using default ADMIN_PASSWORD. Please set a secure password.")

scheduler_service = SchedulerService()

# Metrics are now defined in monitoring/metrics.py
# Initialize them at startup (see lifespan function)


def is_demo_mode() -> bool:
    return not os.getenv("RAPIDAPI_KEY")


async def scheduled_scan():
    """Run scheduled job scan with monitoring."""
    import time
    logger.info("Running scheduled job scan...")
    
    start_time = time.time()
    db = SessionLocal()
    
    try:
        job_service = JobService(db)
        result = await job_service.run_scan()
        logger.info(f"Scan completed: {result}")
        
        if result.get("success"):
            SCAN_RUNS_TOTAL.labels(status="success").inc()
            # Update timestamp of last successful scan
            LAST_SUCCESSFUL_SCAN_TIMESTAMP.set(time.time())
        else:
            SCAN_RUNS_TOTAL.labels(status="failed").inc()
        
        # Update business metrics after scan
        update_business_metrics()
        
    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        SCAN_RUNS_TOTAL.labels(status="error").inc()
        SCAN_ERRORS.labels(error_type=type(e).__name__).inc()
    finally:
        duration = time.time() - start_time
        SCAN_DURATION.observe(duration)
        db.close()
        logger.info(f"Scan completed in {duration:.2f}s")


async def scheduled_cleanup():
    logger.info("Running scheduled cleanup...")
    db = SessionLocal()
    try:
        job_service = JobService(db)
        # Mark jobs older than 7 days as stale (likely expired)
        stale = job_service.mark_stale_jobs(days=7)
        # Delete jobs older than 30 days
        deleted = job_service.cleanup_old_jobs(days=30)
        logger.info(f"Cleanup completed: {stale} jobs marked stale, {deleted} old jobs removed")
    except Exception as e:
        logger.error(f"Cleanup error: {e}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with monitoring initialization."""
    Base.metadata.create_all(bind=engine)
    
    # Initialize monitoring metrics
    update_uptime = initialize_metrics()
    logger.info("Monitoring metrics initialized")
    
    # Schedule periodic metrics updates (every 30 seconds)
    def update_all_metrics():
        update_business_metrics()
        update_connection_pool_metrics(engine)
        update_uptime()
    
    # Update metrics immediately on startup
    update_all_metrics()
    
    # Schedule regular updates using the scheduler's internal add_job method
    scheduler_service.scheduler.add_job(
        update_all_metrics,
        trigger='interval',
        seconds=30,
        id='metrics_update',
        name='Update Prometheus metrics'
    )

    # Schedule scan and cleanup jobs
    scheduler_service.add_scan_job_on_days(scheduled_scan, days=SCAN_DAYS, hour=SCAN_HOUR)
    scheduler_service.add_cleanup_job(scheduled_cleanup, hour=3, minute=0)
    scheduler_service.start()

    logger.info(f"Scheduler started: Scanning on {SCAN_DAYS.upper()} at {SCAN_HOUR}:00 UTC")
    logger.info("Cleanup runs daily at 3:00 AM UTC (removes jobs older than 30 days)")
    logger.info("Metrics update every 30 seconds")
    
    yield
    
    scheduler_service.shutdown()
    logger.info("Application shutdown complete")


app = FastAPI(title="IAM Job Scout", lifespan=lifespan)

# Add monitoring middleware FIRST (order matters!)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Expose Prometheus metrics endpoint
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


def get_current_user(request: Request) -> Optional[str]:
    return request.session.get("user")


def verify_api_token(x_admin_token: Optional[str] = Header(None)) -> bool:
    if not ADMIN_API_TOKEN:
        # No API token configured - require session auth instead
        return False
    if x_admin_token and x_admin_token == ADMIN_API_TOKEN:
        return True
    return False


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    q: str = Query("", description="Search query"),
    location: str = Query("", description="Filter by location"),
    sort: str = Query("newest", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    filter: str = Query("", description="Quick filter: today, high_score, remote")
):
    user = get_current_user(request)
    job_service = JobService(db)

    per_page = 20
    jobs, total_jobs = job_service.search_jobs(
        query=q,
        location=location,
        sort=sort,
        page=page,
        per_page=per_page,
        quick_filter=filter
    )

    stats = job_service.get_job_stats()
    latest_scan = job_service.get_latest_scan()
    locations = job_service.get_unique_locations()

    total_pages = (total_jobs + per_page - 1) // per_page

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "demo_mode": is_demo_mode(),
        "stats": stats,
        "latest_scan": latest_scan,
        "jobs": jobs,
        "total_jobs": total_jobs,
        "locations": locations,
        "current_query": q,
        "current_location": location,
        "current_sort": sort,
        "current_filter": filter,
        "current_page": page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "scan_days": SCAN_DAYS,
        "scan_hour": SCAN_HOUR
    })


@app.get("/job/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    similar_jobs = job_service.get_similar_jobs(job, limit=5)
    
    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "user": user,
        "job": job,
        "similar_jobs": similar_jobs,
        "demo_mode": is_demo_mode()
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["user"] = "admin"
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid password"
    })


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.post("/admin/run-scan")
async def run_scan(
    request: Request,
    db: Session = Depends(get_db),
    x_admin_token: Optional[str] = Header(None)
):
    user = get_current_user(request)
    if not user and not verify_api_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    job_service = JobService(db)
    result = await job_service.run_scan()
    
    if request.headers.get("accept") == "application/json":
        return result
    return RedirectResponse(url="/?scan_completed=1", status_code=303)


@app.post("/admin/cleanup")
async def cleanup_old_jobs(
    request: Request,
    db: Session = Depends(get_db),
    x_admin_token: Optional[str] = Header(None)
):
    user = get_current_user(request)
    if not user and not verify_api_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    job_service = JobService(db)
    deleted_count = job_service.cleanup_old_jobs(days=30)
    
    if request.headers.get("accept") == "application/json":
        return {"success": True, "deleted": deleted_count}
    return RedirectResponse(url="/?cleanup_completed=1", status_code=303)


@app.get("/api/jobs")
async def api_get_jobs(
    db: Session = Depends(get_db), 
    q: str = "",
    location: str = "",
    sort: str = "newest",
    page: int = 1,
    per_page: int = 20
):
    job_service = JobService(db)
    jobs, total = job_service.search_jobs(q, location, sort, page, per_page)
    return {
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "snippet": job.snippet,
                "url": job.url,
                "score": job.score,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@app.get("/api/stats")
async def api_get_stats(db: Session = Depends(get_db)):
    job_service = JobService(db)
    return {
        "stats": job_service.get_job_stats(),
        "demo_mode": is_demo_mode(),
        "scan_days": SCAN_DAYS,
        "scan_hour": SCAN_HOUR
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/job/{job_id}/status")
async def update_job_status(
    request: Request,
    job_id: int,
    status: str = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update a job's status (save, apply, hide)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    job_service = JobService(db)
    job = job_service.update_job_status(job_id, status, notes)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found or invalid status")
    
    # Track status updates in metrics
    JOB_STATUS_UPDATES.labels(status=status).inc()
    
    # Update business metrics to reflect the change
    update_business_metrics()

    if request.headers.get("accept") == "application/json":
        return {"success": True, "job_id": job_id, "status": status}
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)


@app.post("/job/{job_id}/notes")
async def update_job_notes(
    request: Request,
    job_id: int,
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update just the notes for a job"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    job_service = JobService(db)
    job = job_service.update_job_notes(job_id, notes)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if request.headers.get("accept") == "application/json":
        return {"success": True, "job_id": job_id, "notes": notes}
    return RedirectResponse(url=request.headers.get("referer", "/saved"), status_code=303)


@app.get("/saved", response_class=HTMLResponse)
async def saved_jobs(request: Request, db: Session = Depends(get_db)):
    """View saved jobs"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    job_service = JobService(db)
    saved = job_service.get_jobs_by_status("saved")
    applied = job_service.get_jobs_by_status("applied")

    return templates.TemplateResponse("saved_jobs.html", {
        "request": request,
        "user": user,
        "saved_jobs": saved,
        "applied_jobs": applied,
        "demo_mode": is_demo_mode()
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
