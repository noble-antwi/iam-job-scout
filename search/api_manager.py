import asyncio
from typing import List, Dict, Tuple
from search.jsearch import JSearchAPI
from search.remoteok import RemoteOKAPI
from search.adzuna import AdzunaAPI


class APIManager:
    """
    Manages multiple job search APIs and aggregates their results.
    Handles API availability and rate limiting.
    """

    def __init__(self):
        self.jsearch = JSearchAPI()
        self.remoteok = RemoteOKAPI()
        self.adzuna = AdzunaAPI()

    def get_available_apis(self) -> List[str]:
        """Return list of configured/available APIs."""
        available = []
        if self.jsearch.is_configured():
            available.append("jsearch")
        if self.remoteok.is_configured():
            available.append("remoteok")
        if self.adzuna.is_configured():
            available.append("adzuna")
        return available

    def get_api_status(self) -> List[Dict]:
        """Return detailed status of all APIs for dashboard display."""
        return [
            {
                "name": "JSearch",
                "id": "jsearch",
                "configured": self.jsearch.is_configured(),
                "description": "Indeed, LinkedIn, Glassdoor",
                "queries": len(self.jsearch.get_search_queries()) if self.jsearch.is_configured() else 0
            },
            {
                "name": "Adzuna",
                "id": "adzuna",
                "configured": self.adzuna.is_configured(),
                "description": "250 free requests/month",
                "queries": len(self.adzuna.get_search_queries()) if self.adzuna.is_configured() else 0
            },
            {
                "name": "RemoteOK",
                "id": "remoteok",
                "configured": True,  # Always available
                "description": "Remote jobs only",
                "queries": 1  # Single API call
            }
        ]

    async def search_all(self) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Search all available APIs and aggregate results.

        Returns:
            Tuple of (all_jobs, api_stats)
            where api_stats is {api_name: job_count}
        """
        all_jobs = []
        api_stats = {}

        # Run API searches concurrently
        tasks = []

        # JSearch - if configured
        if self.jsearch.is_configured():
            tasks.append(("jsearch", self._search_jsearch()))

        # RemoteOK - always available (no auth needed)
        tasks.append(("remoteok", self._search_remoteok()))

        # Adzuna - if configured
        if self.adzuna.is_configured():
            tasks.append(("adzuna", self._search_adzuna()))

        # Execute all searches concurrently
        if tasks:
            results = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )

            for (api_name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    print(f"API {api_name} failed: {result}")
                    api_stats[api_name] = 0
                else:
                    all_jobs.extend(result)
                    api_stats[api_name] = len(result)

        return all_jobs, api_stats

    async def _search_jsearch(self) -> List[Dict]:
        """Run all JSearch queries with rate limiting to avoid 429 errors."""
        all_results = []
        queries = self.jsearch.get_search_queries()
        rate_limit_delay = 1.0  # 1 second between requests

        for i, query in enumerate(queries):
            try:
                results = await self.jsearch.search(query)
                all_results.extend(results)

                # Add delay between requests to respect rate limits
                if i < len(queries) - 1:
                    await asyncio.sleep(rate_limit_delay)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    # Rate limited - increase delay and retry after pause
                    print(f"JSearch rate limited, pausing for 5 seconds...")
                    await asyncio.sleep(5)
                    rate_limit_delay = min(rate_limit_delay + 0.5, 3.0)
                else:
                    print(f"JSearch query '{query}' failed: {e}")
                continue

        return all_results

    async def _search_remoteok(self) -> List[Dict]:
        """
        Search RemoteOK API.
        RemoteOK returns all jobs at once, so we just make one call.
        """
        try:
            return await self.remoteok.search()
        except Exception as e:
            print(f"RemoteOK search failed: {e}")
            return []

    async def _search_adzuna(self) -> List[Dict]:
        """
        Run Adzuna queries with rate limiting.
        Limited queries due to 250/month limit.
        """
        all_results = []
        queries = self.adzuna.get_search_queries()

        for i, query in enumerate(queries):
            try:
                results = await self.adzuna.search(query)
                all_results.extend(results)

                # Small delay between requests
                if i < len(queries) - 1:
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Adzuna query '{query}' failed: {e}")
                continue

        return all_results
