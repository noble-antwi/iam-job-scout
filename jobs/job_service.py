from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from db.models import Job, ScanRun
from search.jsearch import JSearchAPI


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

                existing = self.db.query(Job).filter(Job.url == url).first()
                if not existing:
                    job = Job(
                        title=job_data["title"],
                        company=job_data.get("company"),
                        location=job_data.get("location"),
                        snippet=job_data.get("snippet"),
                        url=url,
                        source=job_data.get("source", "jsearch"),
                        score=job_data.get("score", 0.0),
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
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Job], int]:
        q = self.db.query(Job)
        
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
        locations = self.db.query(Job.location).distinct().all()
        return sorted([loc[0] for loc in locations if loc[0]])

    def cleanup_old_jobs(self, days: int = 30) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(Job).filter(Job.created_at < cutoff_date).delete()
        self.db.commit()
        return deleted

    def get_all_jobs(self, limit: int = 100) -> List[Job]:
        return self.db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()

    def get_latest_scan(self) -> Optional[ScanRun]:
        return self.db.query(ScanRun).order_by(ScanRun.id.desc()).first()

    def get_job_stats(self) -> Dict:
        total_jobs = self.db.query(Job).count()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_this_week = self.db.query(Job).filter(Job.created_at >= week_ago).count()
        
        locations = self.db.query(Job.location).distinct().count()

        return {
            "total_jobs": total_jobs,
            "new_this_week": new_this_week,
            "locations": locations
        }
