import re
from typing import Dict, List, Tuple


class JobFilter:
    EXCLUDE_KEYWORDS = [
        'senior', 'sr.', 'sr ', 'principal', 'architect', 'lead', 'manager',
        'director', 'head', 'vp', 'vice president', 'staff', 'distinguished',
        'chief', 'executive', 'president', 'cto', 'ciso', 'cio'
    ]

    INCLUDE_KEYWORDS = [
        'analyst', 'associate', 'administrator', 'engineer', 'specialist',
        'iam', 'identity', 'okta', 'entra', 'azure ad', 'sso', 'saml',
        'oidc', 'scim', 'iga', 'pam', 'sailpoint', 'saviynt', 'ping',
        'cyberark', 'access management', 'identity management'
    ]

    INCLUDE_EXPERIENCE = ['0-5', '1-3', '2-4', '3-5', '0-3', '1-4', '2-5', 'entry', 'junior', 'mid']
    EXCLUDE_EXPERIENCE = ['7+', '8+', '10+', '12+', '15+', '7 years', '8 years', '10 years', '12 years']

    @classmethod
    def is_junior_mid_role(cls, title: str, snippet: str = "") -> Tuple[bool, float]:
        combined_text = f"{title} {snippet}".lower()

        for keyword in cls.EXCLUDE_KEYWORDS:
            if keyword.lower() in combined_text:
                return False, 0.0

        for exp in cls.EXCLUDE_EXPERIENCE:
            if exp.lower() in combined_text:
                return False, 0.0

        score = 0.0

        for keyword in cls.INCLUDE_KEYWORDS:
            if keyword.lower() in combined_text:
                score += 10.0

        for exp in cls.INCLUDE_EXPERIENCE:
            if exp.lower() in combined_text:
                score += 5.0

        if 'junior' in combined_text or 'entry' in combined_text:
            score += 15.0
        elif 'mid' in combined_text or 'associate' in combined_text:
            score += 10.0

        if score > 0:
            return True, score

        iam_terms = ['iam', 'identity', 'access management', 'sso', 'authentication']
        if any(term in combined_text for term in iam_terms):
            return True, 5.0

        return False, 0.0

    @classmethod
    def extract_company(cls, title: str, snippet: str, url: str) -> str:
        known_companies = [
            'Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'Netflix',
            'IBM', 'Oracle', 'Salesforce', 'ServiceNow', 'Workday',
            'Okta', 'SailPoint', 'CyberArk', 'Ping Identity', 'ForgeRock',
            'Saviynt', 'One Identity', 'SecureAuth', 'Auth0'
        ]

        combined = f"{title} {snippet}".lower()
        for company in known_companies:
            if company.lower() in combined:
                return company

        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            if 'linkedin' not in domain and 'indeed' not in domain and 'glassdoor' not in domain:
                return domain.split('.')[0].capitalize()

        return "Unknown"

    @classmethod
    def extract_location(cls, snippet: str) -> str:
        us_states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]

        cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'San Francisco', 'Seattle', 'Denver', 'Austin', 'Boston',
            'Atlanta', 'Miami', 'Dallas', 'San Diego', 'San Jose',
            'Washington DC', 'Philadelphia', 'Portland', 'Charlotte'
        ]

        if 'remote' in snippet.lower():
            return 'Remote'

        for city in cities:
            if city.lower() in snippet.lower():
                return f"{city}, USA"

        for state in us_states:
            pattern = rf'\b{state}\b'
            if re.search(pattern, snippet):
                return f"{state}, USA"

        return "USA"
