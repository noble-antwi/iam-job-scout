from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scan_job_id = "scheduled_scan"
        self.cleanup_job_id = "daily_cleanup"

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def add_scan_job_on_days(self, func: Callable, days: str = "mon,wed,sat", hour: int = 6):
        if self.scheduler.get_job(self.scan_job_id):
            self.scheduler.remove_job(self.scan_job_id)

        self.scheduler.add_job(
            func,
            CronTrigger(day_of_week=days, hour=hour, minute=0),
            id=self.scan_job_id,
            name=f"Job Scan ({days.upper()} at {hour}:00)",
            replace_existing=True
        )

    def add_scan_job(self, func: Callable, interval_hours: int = 84):
        if self.scheduler.get_job(self.scan_job_id):
            self.scheduler.remove_job(self.scan_job_id)

        self.scheduler.add_job(
            func,
            IntervalTrigger(hours=interval_hours),
            id=self.scan_job_id,
            name=f"Job Scan (every {interval_hours}h)",
            replace_existing=True
        )

    def add_cleanup_job(self, func: Callable, hour: int = 3, minute: int = 0):
        if self.scheduler.get_job(self.cleanup_job_id):
            self.scheduler.remove_job(self.cleanup_job_id)

        self.scheduler.add_job(
            func,
            CronTrigger(hour=hour, minute=minute),
            id=self.cleanup_job_id,
            name="Daily Cleanup (3:00 AM)",
            replace_existing=True
        )

    def get_jobs_info(self) -> list:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            })
        return jobs

    def remove_job(self, job_id: str) -> bool:
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            return True
        return False
