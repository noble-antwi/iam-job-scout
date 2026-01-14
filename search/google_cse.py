import os
import httpx
from typing import List, Dict, Optional
from search.filters import JobFilter


class GoogleCSESearch:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_CSE_API_KEY", "")
        self.cx = os.getenv("GOOGLE_CSE_CX", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.cx)

    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        if not self.is_configured():
            return self._get_demo_results()

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(num_results, 10),
            "gl": "us",
            "lr": "lang_en"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                return self._parse_results(data)
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _parse_results(self, data: dict) -> List[Dict]:
        results = []
        items = data.get("items", [])

        for item in items:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("link", "")

            is_valid, score = JobFilter.is_junior_mid_role(title, snippet)
            if not is_valid:
                continue

            company = JobFilter.extract_company(title, snippet, url)
            location = JobFilter.extract_location(snippet)

            results.append({
                "title": title,
                "snippet": snippet,
                "url": url,
                "company": company,
                "location": location,
                "score": score,
                "source": "google_cse"
            })

        return results

    def _get_demo_results(self) -> List[Dict]:
        return [
            {
                "title": "IAM Analyst - Entry Level",
                "snippet": "Looking for an entry-level IAM Analyst to join our security team. Experience with Okta and Azure AD preferred. 0-2 years experience required.",
                "url": "https://example.com/job/iam-analyst-1",
                "company": "TechCorp",
                "location": "Remote",
                "score": 35.0,
                "source": "demo"
            },
            {
                "title": "Identity & Access Management Engineer",
                "snippet": "Join our IAM team as an engineer. Work with SailPoint, SAML, and OIDC. 1-3 years experience in identity management.",
                "url": "https://example.com/job/iam-engineer-2",
                "company": "SecureTech",
                "location": "San Francisco, USA",
                "score": 45.0,
                "source": "demo"
            },
            {
                "title": "Associate IAM Specialist",
                "snippet": "Entry level position for IAM specialist. Knowledge of SSO, SCIM, and PAM solutions. Training provided. 0-3 years experience.",
                "url": "https://example.com/job/iam-specialist-3",
                "company": "CloudSecure",
                "location": "Austin, USA",
                "score": 50.0,
                "source": "demo"
            },
            {
                "title": "Junior Identity Management Administrator",
                "snippet": "We're hiring a junior administrator for our identity management team. Experience with CyberArk and Saviynt a plus. 1-4 years experience.",
                "url": "https://example.com/job/iam-admin-4",
                "company": "DataGuard",
                "location": "New York, USA",
                "score": 55.0,
                "source": "demo"
            },
            {
                "title": "IAM Security Analyst - Mid Level",
                "snippet": "Mid-level IAM Security Analyst needed. Work with Ping Identity, Azure AD, and Entra. 2-4 years of IAM experience required.",
                "url": "https://example.com/job/iam-security-5",
                "company": "CyberShield",
                "location": "Boston, USA",
                "score": 40.0,
                "source": "demo"
            }
        ]

    def get_search_queries(self) -> List[str]:
        return [
            'IAM analyst job USA junior entry level',
            'identity access management engineer job USA 0-5 years',
            'Okta administrator job USA associate',
            'Azure AD specialist job USA entry level',
            'SailPoint engineer job USA junior',
            'CyberArk administrator job USA',
            'identity management analyst job USA',
            'SSO specialist job USA entry level',
            'PAM administrator job USA junior',
            'IAM engineer job USA associate'
        ]
