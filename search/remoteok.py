import httpx
from typing import List, Dict
from search.filters import JobFilter


class RemoteOKAPI:
    """
    RemoteOK API - Free, no authentication required.
    Returns remote-only jobs which is a nice complement to JSearch.
    Rate limit: Be respectful, no more than 1 request per second.
    """

    BASE_URL = "https://remoteok.com/api"

    def __init__(self):
        pass

    def is_configured(self) -> bool:
        # No API key needed
        return True

    async def search(self, tags: List[str] = None) -> List[Dict]:
        """
        Fetch jobs from RemoteOK API.
        The API returns all jobs; we filter locally for security/IAM roles.
        """
        headers = {
            "User-Agent": "IAMJobScout/1.0 (job aggregator for security roles)"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_results(data)
        except Exception as e:
            print(f"RemoteOK error: {e}")
            return []

    def _parse_results(self, data: list) -> List[Dict]:
        """
        Parse RemoteOK API response.
        First item is usually metadata, actual jobs start from index 1.
        """
        results = []

        # Skip first item (legal notice) if it exists
        jobs = data[1:] if len(data) > 1 else data

        for job in jobs:
            if not isinstance(job, dict):
                continue

            # Get job details
            title = job.get("position", "")
            company = job.get("company", "Unknown")
            description = job.get("description", "")[:1500] if job.get("description") else ""
            tags = job.get("tags", [])

            # Check if this is a security/IAM related job
            combined_text = f"{title} {description} {' '.join(tags)}".lower()

            # Quick filter: must have at least one security/IAM keyword
            security_keywords = [
                'security', 'iam', 'identity', 'cybersecurity', 'infosec',
                'soc', 'compliance', 'audit', 'risk', 'threat', 'vulnerability',
                'penetration', 'forensic', 'incident', 'devsecops', 'secops',
                'okta', 'azure ad', 'active directory', 'sso', 'saml'
            ]

            if not any(kw in combined_text for kw in security_keywords):
                continue

            # Apply the standard job filter
            is_valid, score = JobFilter.is_junior_mid_role(title, description)
            if not is_valid:
                continue

            # Build the job URL
            job_id = job.get("id", "")
            slug = job.get("slug", "")
            url = job.get("url", f"https://remoteok.com/remote-jobs/{job_id}-{slug}" if job_id else "")

            # Extract salary if available
            salary_min = None
            salary_max = None
            if job.get("salary_min"):
                try:
                    salary_min = float(job.get("salary_min"))
                except (ValueError, TypeError):
                    pass
            if job.get("salary_max"):
                try:
                    salary_max = float(job.get("salary_max"))
                except (ValueError, TypeError):
                    pass

            results.append({
                "title": title,
                "company": company,
                "location": "Remote",  # All RemoteOK jobs are remote
                "snippet": description,
                "url": url,
                "source": "remoteok",
                "score": score,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "job_type": "FULLTIME",  # RemoteOK focuses on full-time
                "posted_at": job.get("date", ""),
                "tags": tags
            })

        return results
