from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from functools import lru_cache
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func
from db.models import Job, ScanRun
from search.jsearch import JSearchAPI


# Simple in-memory cache for stats (refreshes every 5 minutes)
_stats_cache = {"data": None, "expires": None}
_locations_cache = {"data": None, "expires": None}
CACHE_TTL = timedelta(minutes=5)


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.search = JSearchAPI()

    async def run_scan(self) -> Dict:
        scan_run = ScanRun(status="running")
        self.db.add(scan_run)
        self.db.commit()
        self.db.refresh(scan_run)

        try:
            all_jobs = []
            queries = self.search.get_search_queries()

            for query in queries:
                results = await self.search.search(query)
                all_jobs.extend(results)

            new_jobs = 0
            total_found = len(all_jobs)
            seen_urls: Set[str] = set()

            for job_data in all_jobs:
                url = job_data.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                # Check for exact URL match
                existing = self.db.query(Job).filter(Job.url == url).first()
                if existing:
                    continue

                # Check for duplicate by title + company (same job posted multiple times)
                title = job_data["title"]
                company = job_data.get("company", "")
                if title and company:
                    duplicate = self.db.query(Job).filter(
                        Job.title == title,
                        Job.company == company
                    ).first()
                    if duplicate:
                        continue

                if not existing:
                    job = Job(
                        title=job_data["title"],
                        company=job_data.get("company"),
                        location=job_data.get("location"),
                        snippet=job_data.get("snippet"),
                        url=url,
                        source=job_data.get("source", "jsearch"),
                        score=job_data.get("score", 0.0),
                        salary_min=job_data.get("salary_min"),
                        salary_max=job_data.get("salary_max"),
                        job_type=job_data.get("job_type"),
                        is_new=True
                    )
                    self.db.add(job)
                    new_jobs += 1

            self.db.commit()

            scan_run.completed_at = datetime.utcnow()
            scan_run.jobs_found = total_found
            scan_run.new_jobs = new_jobs
            scan_run.status = "completed"
            self.db.commit()

            return {
                "success": True,
                "scan_id": scan_run.id,
                "jobs_found": total_found,
                "new_jobs": new_jobs
            }
        except Exception as e:
            self.db.rollback()
            try:
                scan_run = self.db.query(ScanRun).filter(ScanRun.id == scan_run.id).first()
                if scan_run:
                    scan_run.status = "failed"
                    scan_run.error_message = str(e)
                    scan_run.completed_at = datetime.utcnow()
                    self.db.commit()
            except:
                pass
            return {"success": False, "error": str(e)}

    def search_jobs(
        self,
        query: str = "",
        location: str = "",
        sort: str = "newest",
        status: str = "",  # Filter by job status
        page: int = 1,
        per_page: int = 20,
        exclude_hidden: bool = True,  # By default, don't show hidden jobs
        quick_filter: str = ""  # Quick filters: today, high_score, remote
    ) -> Tuple[List[Job], int]:
        q = self.db.query(Job)

        # Exclude hidden jobs by default
        if exclude_hidden:
            q = q.filter(Job.status != 'hidden')

        # Filter by status if specified
        if status:
            q = q.filter(Job.status == status)

        # Apply quick filters
        if quick_filter == "today":
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(Job.created_at >= today_start)
        elif quick_filter == "high_score":
            q = q.filter(Job.score >= 70)
        elif quick_filter == "remote":
            q = q.filter(or_(
                Job.location.ilike("%remote%"),
                Job.snippet.ilike("%remote%"),
                Job.snippet.ilike("%work from home%")
            ))

        if query:
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    Job.title.ilike(search_term),
                    Job.company.ilike(search_term),
                    Job.snippet.ilike(search_term)
                )
            )

        if location:
            q = q.filter(Job.location.ilike(f"%{location}%"))

        if sort == "newest":
            q = q.order_by(desc(Job.created_at))
        elif sort == "oldest":
            q = q.order_by(asc(Job.created_at))
        elif sort == "relevance":
            q = q.order_by(desc(Job.score))
        elif sort == "company":
            q = q.order_by(asc(Job.company))

        total = q.count()

        offset = (page - 1) * per_page
        jobs = q.offset(offset).limit(per_page).all()

        return jobs, total

    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_similar_jobs(self, job: Job, limit: int = 5) -> List[Job]:
        keywords = []
        if job.company:
            keywords.append(job.company)
        if job.location:
            keywords.append(job.location)
        
        q = self.db.query(Job).filter(Job.id != job.id)
        
        if keywords:
            conditions = []
            for keyword in keywords:
                conditions.append(Job.title.ilike(f"%{keyword}%"))
                conditions.append(Job.company.ilike(f"%{keyword}%"))
                conditions.append(Job.location.ilike(f"%{keyword}%"))
            q = q.filter(or_(*conditions))
        
        return q.order_by(desc(Job.score)).limit(limit).all()

    def get_unique_locations(self) -> List[str]:
        global _locations_cache
        now = datetime.utcnow()

        # Return cached data if still valid
        if _locations_cache["data"] and _locations_cache["expires"] and _locations_cache["expires"] > now:
            return _locations_cache["data"]

        # Query and sort in database (more efficient)
        locations = self.db.query(Job.location).distinct().order_by(Job.location).all()
        result = [loc[0] for loc in locations if loc[0]]

        # Update cache
        _locations_cache["data"] = result
        _locations_cache["expires"] = now + CACHE_TTL

        return result

    def cleanup_old_jobs(self, days: int = 30) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(Job).filter(Job.created_at < cutoff_date).delete()
        self.db.commit()
        return deleted

    def mark_stale_jobs(self, days: int = 7) -> int:
        """Mark jobs older than X days as stale (lower priority in listings)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        # Only mark jobs that are still 'new' status (not saved/applied/hidden)
        count = self.db.query(Job).filter(
            Job.created_at < cutoff_date,
            Job.status == 'new'
        ).update({Job.status: 'stale'})
        self.db.commit()
        return count

    def get_all_jobs(self, limit: int = 100) -> List[Job]:
        return self.db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()

    def get_latest_scan(self) -> Optional[ScanRun]:
        return self.db.query(ScanRun).order_by(ScanRun.id.desc()).first()

    def get_job_stats(self) -> Dict:
        global _stats_cache
        now = datetime.utcnow()

        # Return cached data if still valid
        if _stats_cache["data"] and _stats_cache["expires"] and _stats_cache["expires"] > now:
            return _stats_cache["data"]

        total_jobs = self.db.query(Job).filter(Job.status != 'hidden').count()

        week_ago = now - timedelta(days=7)
        new_this_week = self.db.query(Job).filter(
            Job.created_at >= week_ago,
            Job.status != 'hidden'
        ).count()

        locations = self.db.query(Job.location).distinct().count()

        # Count by status
        saved_count = self.db.query(Job).filter(Job.status == 'saved').count()
        applied_count = self.db.query(Job).filter(Job.status == 'applied').count()

        result = {
            "total_jobs": total_jobs,
            "new_this_week": new_this_week,
            "locations": locations,
            "saved_count": saved_count,
            "applied_count": applied_count
        }

        # Update cache
        _stats_cache["data"] = result
        _stats_cache["expires"] = now + CACHE_TTL

        return result

    def update_job_status(self, job_id: int, status: str, notes: str = None) -> Optional[Job]:
        """Update a job's status (new, saved, applied, hidden)"""
        global _stats_cache
        job = self.get_job_by_id(job_id)
        if not job:
            return None

        valid_statuses = ['new', 'saved', 'applied', 'hidden', 'stale']
        if status not in valid_statuses:
            return None

        job.status = status
        if notes is not None:
            job.notes = notes
        self.db.commit()

        # Invalidate stats cache
        _stats_cache["data"] = None

        return job

    def get_jobs_by_status(self, status: str, limit: int = 100) -> List[Job]:
        """Get jobs by their status"""
        return self.db.query(Job).filter(
            Job.status == status
        ).order_by(desc(Job.created_at)).limit(limit).all()

    def update_job_notes(self, job_id: int, notes: str) -> Optional[Job]:
        """Update just the notes for a job"""
        job = self.get_job_by_id(job_id)
        if not job:
            return None
        job.notes = notes
        self.db.commit()
        return job
