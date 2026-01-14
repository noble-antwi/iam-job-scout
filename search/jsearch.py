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

    async def search(self, query: str, page: int = 1, num_pages: int = 1) -> List[Dict]:
        if not self.is_configured():
            return self._get_demo_results()

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        params = {
            "query": query,
            "page": str(page),
            "num_pages": str(num_pages),
            "country": "us",
            "date_posted": "week"
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
            description = job.get("job_description", "")[:500] if job.get("job_description") else ""

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

    def _get_demo_results(self) -> List[Dict]:
        return [
            {
                "title": "IAM Analyst - Entry Level",
                "company": "TechCorp",
                "location": "Remote, USA",
                "snippet": "Looking for an entry-level IAM Analyst to join our security team. Experience with Okta and Azure AD preferred. 0-2 years experience required.",
                "url": "https://example.com/job/iam-analyst-1",
                "source": "demo",
                "score": 35.0
            },
            {
                "title": "Identity & Access Management Engineer",
                "company": "SecureTech",
                "location": "San Francisco, CA",
                "snippet": "Join our IAM team as an engineer. Work with SailPoint, SAML, and OIDC. 1-3 years experience in identity management.",
                "url": "https://example.com/job/iam-engineer-2",
                "source": "demo",
                "score": 45.0
            },
            {
                "title": "Associate IAM Specialist",
                "company": "CloudSecure",
                "location": "Austin, TX",
                "snippet": "Entry level position for IAM specialist. Knowledge of SSO, SCIM, and PAM solutions. Training provided. 0-3 years experience.",
                "url": "https://example.com/job/iam-specialist-3",
                "source": "demo",
                "score": 50.0
            },
            {
                "title": "Junior Identity Management Administrator",
                "company": "DataGuard",
                "location": "New York, NY",
                "snippet": "We're hiring a junior administrator for our identity management team. Experience with CyberArk and Saviynt a plus. 1-4 years experience.",
                "url": "https://example.com/job/iam-admin-4",
                "source": "demo",
                "score": 55.0
            },
            {
                "title": "IAM Security Analyst - Mid Level",
                "company": "CyberShield",
                "location": "Boston, MA",
                "snippet": "Mid-level IAM Security Analyst needed. Work with Ping Identity, Azure AD, and Entra. 2-4 years of IAM experience required.",
                "url": "https://example.com/job/iam-security-5",
                "source": "demo",
                "score": 40.0
            },
            {
                "title": "Okta Administrator - Junior",
                "company": "IdentityFirst",
                "location": "Seattle, WA",
                "snippet": "Looking for a junior Okta administrator. Will work on SSO implementations and user lifecycle management. 1-2 years experience.",
                "url": "https://example.com/job/okta-admin-6",
                "source": "demo",
                "score": 52.0
            },
            {
                "title": "Azure AD Specialist - Entry Level",
                "company": "CloudWorks",
                "location": "Denver, CO",
                "snippet": "Entry-level position managing Azure Active Directory and Entra ID. Knowledge of conditional access policies preferred.",
                "url": "https://example.com/job/azure-ad-7",
                "source": "demo",
                "score": 48.0
            },
            {
                "title": "Identity Governance Analyst",
                "company": "SecureAccess Inc",
                "location": "Chicago, IL",
                "snippet": "Join our IGA team. Work with SailPoint IdentityNow. 2-4 years experience in identity governance and access certifications.",
                "url": "https://example.com/job/iga-analyst-8",
                "source": "demo",
                "score": 42.0
            }
        ]

    def get_search_queries(self) -> List[str]:
        return [
            "IAM analyst entry level USA",
            "identity access management engineer junior USA",
            "Okta administrator USA",
            "Azure AD specialist USA",
            "SailPoint engineer USA",
            "identity management analyst USA",
            "SSO specialist entry level USA",
            "CyberArk administrator junior USA",
            "IAM security analyst USA",
            "access management engineer USA"
        ]
