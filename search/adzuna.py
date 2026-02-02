import os
import httpx
from typing import List, Dict
from search.filters import JobFilter


class AdzunaAPI:
    """
    Adzuna API - Free tier: 250 requests/month
    Good coverage of US job market with structured data.
    Sign up at: https://developer.adzuna.com/
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_key)

    async def search(self, query: str, page: int = 1, results_per_page: int = 50) -> List[Dict]:
        """
        Search Adzuna for jobs matching the query.
        """
        if not self.is_configured():
            return []

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": results_per_page,
            "what": query,
            "max_days_old": 30  # Jobs from last 30 days
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/{page}",
                    params=params,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_results(data)
        except Exception as e:
            print(f"Adzuna error: {e}")
            return []

    def _parse_results(self, data: dict) -> List[Dict]:
        """Parse Adzuna API response."""
        results = []
        jobs = data.get("results", [])

        for job in jobs:
            title = job.get("title", "")
            description = job.get("description", "")[:1500] if job.get("description") else ""

            # Apply job filter
            is_valid, score = JobFilter.is_junior_mid_role(title, description)
            if not is_valid:
                continue

            # Extract location
            location_data = job.get("location", {})
            location_parts = []
            if location_data.get("area"):
                # Adzuna returns location as nested arrays
                areas = location_data.get("area", [])
                if areas:
                    location_parts = [a for a in areas if a]
            location = ", ".join(location_parts[-2:]) if location_parts else "USA"

            # Extract salary
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")

            results.append({
                "title": title,
                "company": job.get("company", {}).get("display_name", "Unknown"),
                "location": location,
                "snippet": description,
                "url": job.get("redirect_url", ""),
                "source": "adzuna",
                "score": score,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "job_type": job.get("contract_type", ""),
                "posted_at": job.get("created", "")
            })

        return results

    def get_search_queries(self) -> List[str]:
        """
        Optimized queries for Adzuna (fewer due to 250/month limit).
        Focus on broad queries that return many results.
        """
        return [
            # Core IAM - broad queries
            "identity access management",
            "IAM analyst",
            "Okta administrator",
            "SailPoint",
            "CyberArk",

            # Cybersecurity - broad queries
            "cybersecurity analyst",
            "security analyst",
            "SOC analyst",
            "security engineer",

            # Cloud security
            "cloud security",
            "AWS security",
            "DevSecOps",

            # GRC
            "GRC analyst",
            "compliance analyst",
        ]
