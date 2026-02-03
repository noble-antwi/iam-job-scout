"""
Basic import and smoke tests for IAM Job Scout.
Run with: python -m pytest tests/ -v
"""
import pytest


class TestImports:
    """Test that all modules can be imported without errors."""

    def test_import_search_modules(self):
        from search import (
            JobFilter,
            JSearchAPI,
            AdzunaAPI,
            RemoteOKAPI,
            APIManager,
            JobDeduplicator,
        )
        assert JobFilter is not None
        assert JSearchAPI is not None
        assert AdzunaAPI is not None
        assert RemoteOKAPI is not None
        assert APIManager is not None
        assert JobDeduplicator is not None

    def test_import_db_modules(self):
        from db.database import engine, Base, get_db
        from db.models import Job, ScanRun, Settings
        assert engine is not None
        assert Job is not None
        assert ScanRun is not None

    def test_import_job_service(self):
        from jobs.job_service import JobService
        assert JobService is not None

    def test_import_scheduler(self):
        from scheduler.scheduler_service import SchedulerService
        assert SchedulerService is not None


class TestAPIManager:
    """Test APIManager functionality."""

    def test_api_manager_init(self):
        from search import APIManager
        manager = APIManager()
        assert manager.jsearch is not None
        assert manager.adzuna is not None
        assert manager.remoteok is not None

    def test_get_api_status(self):
        from search import APIManager
        manager = APIManager()
        status = manager.get_api_status()
        assert isinstance(status, list)
        assert len(status) == 3
        assert all("name" in api for api in status)
        assert all("configured" in api for api in status)

    def test_remoteok_always_configured(self):
        from search import APIManager
        manager = APIManager()
        status = manager.get_api_status()
        remoteok = next(api for api in status if api["id"] == "remoteok")
        assert remoteok["configured"] is True


class TestDeduplication:
    """Test deduplication logic."""

    def test_normalize_company(self):
        from search import JobDeduplicator
        assert JobDeduplicator.normalize_company("Acme Inc.") == "acme"
        assert JobDeduplicator.normalize_company("Tech Corp") == "tech"
        assert JobDeduplicator.normalize_company("  Company LLC  ") == "company"

    def test_normalize_title(self):
        from search import JobDeduplicator
        result = JobDeduplicator.normalize_title("Sr. Security Engineer - Remote")
        assert "senior" in result
        assert "security" in result
        assert "engineer" in result

    def test_duplicate_detection(self):
        from search import JobDeduplicator
        job1 = {"title": "Security Analyst", "company": "Acme Inc", "location": "NYC"}
        job2 = {"title": "Security Analyst", "company": "Acme", "location": "New York"}
        is_dup, confidence = JobDeduplicator.is_duplicate(job1, job2)
        assert is_dup is True
        assert confidence > 0.8

    def test_non_duplicate_detection(self):
        from search import JobDeduplicator
        job1 = {"title": "Security Analyst", "company": "Acme", "location": "NYC"}
        job2 = {"title": "Software Engineer", "company": "Google", "location": "SF"}
        is_dup, confidence = JobDeduplicator.is_duplicate(job1, job2)
        assert is_dup is False


class TestJobFilter:
    """Test job filtering logic."""

    def test_valid_junior_role(self):
        from search import JobFilter
        is_valid, score = JobFilter.is_junior_mid_role(
            "Junior Security Analyst",
            "Entry level position for security monitoring"
        )
        assert is_valid is True
        assert score > 0

    def test_senior_role_filtered(self):
        from search import JobFilter
        is_valid, score = JobFilter.is_junior_mid_role(
            "Senior Director of Security",
            "15+ years experience required, VP level"
        )
        assert is_valid is False


class TestQueryCounts:
    """Test that query counts are reasonable."""

    def test_jsearch_query_count(self):
        from search import JSearchAPI
        api = JSearchAPI()
        queries = api.get_search_queries()
        assert len(queries) <= 20, f"JSearch has {len(queries)} queries, should be <= 20"

    def test_adzuna_query_count(self):
        from search import AdzunaAPI
        api = AdzunaAPI()
        queries = api.get_search_queries()
        assert len(queries) <= 15, f"Adzuna has {len(queries)} queries, should be <= 15"
