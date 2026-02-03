import os
import httpx
from typing import List, Dict
from search.filters import JobFilter


class JSearchAPI:
    BASE_URL = "https://jsearch.p.rapidapi.com"

    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, page: int = 1, num_pages: int = 2) -> List[Dict]:
        if not self.is_configured():
            # No API key - return empty list (no demo jobs)
            return []

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        params = {
            "query": query,
            "page": str(page),
            "num_pages": str(num_pages),
            "country": "us",
            "date_posted": "month",  # Expanded from "week" to catch more listings
            "employment_types": "FULLTIME,CONTRACTOR"  # Focus on full-time and contract roles
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_results(data)
        except Exception as e:
            print(f"JSearch error: {e}")
            return []

    def _parse_results(self, data: dict) -> List[Dict]:
        results = []
        jobs = data.get("data", [])

        for job in jobs:
            title = job.get("job_title", "")
            # Use more of the description for better keyword matching
            description = job.get("job_description", "")[:1500] if job.get("job_description") else ""

            is_valid, score = JobFilter.is_junior_mid_role(title, description)
            if not is_valid:
                continue

            city = job.get("job_city", "")
            state = job.get("job_state", "")
            location = f"{city}, {state}" if city and state else city or state or "USA"

            results.append({
                "title": title,
                "company": job.get("employer_name", "Unknown"),
                "location": location,
                "snippet": description,
                "url": job.get("job_apply_link") or job.get("job_google_link", ""),
                "source": "jsearch",
                "score": score,
                "salary_min": job.get("job_min_salary"),
                "salary_max": job.get("job_max_salary"),
                "job_type": job.get("job_employment_type", ""),
                "posted_at": job.get("job_posted_at_datetime_utc", "")
            })

        return results

    def get_search_queries(self) -> List[str]:
        """
        Consolidated search queries for API cost efficiency.
        Reduced to 18 broad queries that maximize coverage.
        Broad queries like "security analyst" capture junior/senior/SOC variants.
        """
        return [
            # ===== IAM (5 queries) =====
            "identity access management",
            "IAM analyst engineer",
            "Okta SailPoint administrator",
            "CyberArk privileged access",
            "Active Directory engineer",

            # ===== CYBERSECURITY (5 queries) =====
            "cybersecurity analyst",
            "security analyst",
            "security engineer",
            "SOC analyst",
            "GRC compliance analyst",

            # ===== CLOUD SECURITY (4 queries) =====
            "cloud security engineer",
            "AWS Azure security engineer",
            "DevSecOps engineer",
            "infrastructure security engineer",

            # ===== SPECIALIZED (4 queries) =====
            "penetration tester",
            "vulnerability analyst",
            "incident response analyst",
            "threat intelligence analyst",
        ]
