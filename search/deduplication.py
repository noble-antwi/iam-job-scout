import re
import hashlib
from typing import Dict, Optional, Tuple
from difflib import SequenceMatcher


class JobDeduplicator:
    """
    Robust job deduplication for multi-API scenarios.
    Handles variations in company names, titles, and URLs across different job boards.
    """

    # Common company name variations to normalize
    COMPANY_SUFFIXES = [
        r'\s*,?\s*(inc\.?|llc\.?|ltd\.?|corp\.?|corporation|company|co\.?|plc\.?|limited|gmbh|ag|sa|nv)\.?\s*$',
        r'\s*\(?formerly\s+[^)]+\)?\s*$',
        r'\s*-\s*(remote|hiring|careers).*$'
    ]

    # Job title noise words to remove for comparison
    TITLE_NOISE = [
        r'\s*-\s*(remote|hybrid|onsite|on-site|contract|full-time|part-time|temp).*$',
        r'\s*\(\s*(remote|hybrid|onsite|on-site|contract|full-time|part-time|temp)[^)]*\)\s*$',
        r'\s*\[\s*[^\]]+\]\s*$',  # Remove bracketed content like [REMOTE]
        r'\s*i{1,3}$',  # Remove Roman numerals I, II, III at end
        r'\s*[123]$',  # Remove numbers at end
    ]

    # Location variations
    LOCATION_ALIASES = {
        'nyc': 'new york',
        'ny': 'new york',
        'la': 'los angeles',
        'sf': 'san francisco',
        'dc': 'washington',
        'washington dc': 'washington',
        'philly': 'philadelphia',
        'chi': 'chicago',
    }

    @classmethod
    def normalize_company(cls, company: str) -> str:
        """Normalize company name for comparison."""
        if not company:
            return ""

        normalized = company.lower().strip()

        # Remove common suffixes
        for pattern in cls.COMPANY_SUFFIXES:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    @classmethod
    def normalize_title(cls, title: str) -> str:
        """Normalize job title for comparison."""
        if not title:
            return ""

        normalized = title.lower().strip()

        # Remove noise patterns
        for pattern in cls.TITLE_NOISE:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Standardize common variations (use word boundaries to avoid partial replacements)
        normalized = re.sub(r'\bsr\.?(?=\s|$)', 'senior', normalized)
        normalized = re.sub(r'\bjr\.?(?=\s|$)', 'junior', normalized)
        normalized = re.sub(r'\bmgr\b', 'manager', normalized)
        normalized = re.sub(r'\beng\b', 'engineer', normalized)
        normalized = normalized.replace('&', 'and')

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    @classmethod
    def normalize_location(cls, location: str) -> str:
        """Normalize location for comparison."""
        if not location:
            return ""

        normalized = location.lower().strip()

        # Apply aliases
        for alias, canonical in cls.LOCATION_ALIASES.items():
            if alias in normalized:
                normalized = normalized.replace(alias, canonical)

        # Remove state abbreviations like ", CA" or ", NY"
        normalized = re.sub(r',\s*[a-z]{2}\s*$', '', normalized)

        # Remove "USA", "United States"
        normalized = re.sub(r',?\s*(usa|united states|u\.s\.a?\.?)\s*$', '', normalized, flags=re.IGNORECASE)

        return normalized.strip()

    @classmethod
    def similarity_score(cls, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    @classmethod
    def generate_fingerprint(cls, title: str, company: str, location: str = "") -> str:
        """
        Generate a fingerprint hash for a job based on normalized fields.
        Used for quick duplicate detection.
        """
        norm_title = cls.normalize_title(title)
        norm_company = cls.normalize_company(company)
        norm_location = cls.normalize_location(location)

        # Create a consistent string for hashing
        fingerprint_string = f"{norm_title}|{norm_company}|{norm_location}"
        return hashlib.md5(fingerprint_string.encode()).hexdigest()

    @classmethod
    def is_duplicate(
        cls,
        new_job: Dict,
        existing_job: Dict,
        title_threshold: float = 0.85,
        company_threshold: float = 0.80
    ) -> Tuple[bool, float]:
        """
        Check if two jobs are duplicates using fuzzy matching.

        Returns:
            Tuple of (is_duplicate: bool, confidence: float)
        """
        # Extract fields
        new_title = new_job.get("title", "")
        new_company = new_job.get("company", "")
        new_location = new_job.get("location", "")

        existing_title = existing_job.get("title", "") if isinstance(existing_job, dict) else getattr(existing_job, 'title', '')
        existing_company = existing_job.get("company", "") if isinstance(existing_job, dict) else getattr(existing_job, 'company', '')
        existing_location = existing_job.get("location", "") if isinstance(existing_job, dict) else getattr(existing_job, 'location', '')

        # Normalize fields
        norm_new_title = cls.normalize_title(new_title)
        norm_new_company = cls.normalize_company(new_company)
        norm_new_location = cls.normalize_location(new_location)

        norm_existing_title = cls.normalize_title(existing_title)
        norm_existing_company = cls.normalize_company(existing_company)
        norm_existing_location = cls.normalize_location(existing_location)

        # Calculate similarities
        title_sim = cls.similarity_score(norm_new_title, norm_existing_title)
        company_sim = cls.similarity_score(norm_new_company, norm_existing_company)
        location_sim = cls.similarity_score(norm_new_location, norm_existing_location)

        # Exact fingerprint match is definitely a duplicate
        new_fingerprint = cls.generate_fingerprint(new_title, new_company, new_location)
        existing_fingerprint = cls.generate_fingerprint(existing_title, existing_company, existing_location)

        if new_fingerprint == existing_fingerprint:
            return True, 1.0

        # Check title and company similarity
        if title_sim >= title_threshold and company_sim >= company_threshold:
            # Additional location check for higher confidence
            if location_sim >= 0.6 or not norm_new_location or not norm_existing_location:
                confidence = (title_sim * 0.5) + (company_sim * 0.4) + (location_sim * 0.1)
                return True, confidence

        # Special case: exact company match with very similar title
        if company_sim >= 0.95 and title_sim >= 0.75:
            confidence = (title_sim * 0.5) + (company_sim * 0.5)
            return True, confidence

        return False, 0.0

    @classmethod
    def find_best_match(
        cls,
        new_job: Dict,
        existing_jobs: list,
        title_threshold: float = 0.85,
        company_threshold: float = 0.80
    ) -> Optional[Tuple[object, float]]:
        """
        Find the best matching existing job for a new job.

        Returns:
            Tuple of (best_match_job, confidence) or None if no match found
        """
        best_match = None
        best_confidence = 0.0

        for existing in existing_jobs:
            is_dup, confidence = cls.is_duplicate(
                new_job, existing, title_threshold, company_threshold
            )
            if is_dup and confidence > best_confidence:
                best_match = existing
                best_confidence = confidence

        if best_match:
            return best_match, best_confidence
        return None
