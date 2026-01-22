import re
from typing import Dict, List, Tuple


class JobFilter:
    # Titles that indicate senior-level roles (exclude these)
    EXCLUDE_TITLE_KEYWORDS = [
        'senior', 'sr.', 'sr ', 'principal', 'architect', 'lead', 'manager',
        'director', 'head', 'vp', 'vice president', 'staff', 'distinguished',
        'chief', 'executive', 'president', 'cto', 'ciso', 'cio'
    ]

    # Experience requirements that are too senior (only check in snippet, not title)
    EXCLUDE_EXPERIENCE = [
        '7+ years', '8+ years', '10+ years', '12+ years', '15+ years',
        '7 years', '8 years', '10 years', '12 years', '15 years',
        'minimum 7', 'minimum 8', 'minimum 10', 'at least 7', 'at least 8'
    ]

    # Core IAM technologies and platforms (high value)
    IAM_PLATFORMS = [
        'okta', 'azure ad', 'entra', 'sailpoint', 'saviynt', 'cyberark',
        'ping identity', 'forgerock', 'one identity', 'auth0', 'duo',
        'beyondtrust', 'delinea', 'centrify', 'identitynow',
        # Additional platforms
        'thycotic', 'hashicorp vault', 'keeper', '1password', 'lastpass enterprise',
        'jumpcloud', 'onelogin', 'secureauth', 'radiant logic'
    ]

    # IAM concepts and protocols (medium value)
    IAM_CONCEPTS = [
        'iam', 'identity', 'sso', 'single sign-on', 'saml', 'oidc', 'oauth',
        'scim', 'ldap', 'active directory', 'mfa', 'multi-factor',
        'pam', 'privileged access', 'iga', 'identity governance',
        'access management', 'identity management', 'rbac', 'role-based',
        'joiner mover leaver', 'jml', 'access certification', 'access review',
        'provisioning', 'deprovisioning', 'lifecycle management',
        # Additional terms companies often use
        'user access', 'access control', 'authentication', 'authorization',
        'directory services', 'federation', 'idp', 'identity provider',
        'credential', 'entitlement', 'user lifecycle', 'onboarding',
        'security clearance', 'access request', 'segregation of duties', 'sod',
        # Security analyst context terms
        'user provisioning', 'access governance', 'identity security',
        'zero trust', 'least privilege', 'password management', 'secrets management',
        'service accounts', 'privileged accounts', 'access reviews',
        'identity verification', 'user authentication', 'identity protection'
    ]

    # Security-related terms that indicate IAM overlap (medium value)
    SECURITY_IAM_OVERLAP = [
        'security analyst', 'cybersecurity analyst', 'information security',
        'it security', 'security operations', 'soc analyst', 'grc',
        'compliance analyst', 'audit', 'risk analyst', 'security engineer'
    ]

    # Job titles that indicate good fit (medium value)
    GOOD_TITLES = [
        'analyst', 'associate', 'administrator', 'engineer', 'specialist',
        'consultant', 'coordinator', 'technician', 'support', 'developer',
        'operations', 'ops', 'implementation', 'integration',
        # Additional security-related titles
        'security analyst', 'security engineer', 'security specialist',
        'compliance analyst', 'grc analyst', 'audit analyst'
    ]

    # Experience indicators for junior/mid roles (bonus points)
    JUNIOR_MID_EXPERIENCE = [
        '0-2', '1-3', '2-4', '3-5', '0-3', '1-4', '2-5', '0-5',
        'entry level', 'entry-level', 'junior', 'associate level',
        '1 year', '2 years', '3 years', '4 years', '5 years',
        'new grad', 'recent graduate', 'early career'
    ]

    @classmethod
    def is_junior_mid_role(cls, title: str, snippet: str = "") -> Tuple[bool, float]:
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        combined_text = f"{title_lower} {snippet_lower}"

        # Check for senior-level indicators in the TITLE only
        # (sometimes snippets mention "reports to senior" which is fine)
        for keyword in cls.EXCLUDE_TITLE_KEYWORDS:
            if keyword.lower() in title_lower:
                return False, 0.0

        # Check for high experience requirements in snippet
        for exp in cls.EXCLUDE_EXPERIENCE:
            if exp.lower() in snippet_lower:
                return False, 0.0

        score = 0.0
        matched_reasons = []

        # IAM Platform matches (high value - 20 points each, max 60)
        platform_matches = 0
        for platform in cls.IAM_PLATFORMS:
            if platform in combined_text:
                platform_matches += 1
                if platform_matches <= 3:  # Cap at 3 platforms
                    score += 20.0
                    matched_reasons.append(f"platform:{platform}")

        # IAM Concept matches (medium value - 10 points each, max 40)
        concept_matches = 0
        for concept in cls.IAM_CONCEPTS:
            if concept in combined_text:
                concept_matches += 1
                if concept_matches <= 4:  # Cap at 4 concepts
                    score += 10.0
                    matched_reasons.append(f"concept:{concept}")

        # Good title match (15 points)
        for title_kw in cls.GOOD_TITLES:
            if title_kw in title_lower:
                score += 15.0
                matched_reasons.append(f"title:{title_kw}")
                break  # Only count once

        # Security analyst with IAM overlap (15 points if security role mentions IAM concepts)
        has_security_title = any(term in title_lower for term in cls.SECURITY_IAM_OVERLAP)
        has_iam_in_description = any(concept in snippet_lower for concept in ['iam', 'identity', 'access management', 'provisioning', 'active directory'])
        if has_security_title and has_iam_in_description:
            score += 15.0
            matched_reasons.append("security_iam_overlap")

        # Junior/mid experience indicators (bonus 10 points)
        for exp in cls.JUNIOR_MID_EXPERIENCE:
            if exp in combined_text:
                score += 10.0
                matched_reasons.append(f"experience:{exp}")
                break  # Only count once

        # Remote work bonus (5 points - nice to have)
        if 'remote' in combined_text or 'work from home' in combined_text:
            score += 5.0
            matched_reasons.append("remote")

        # If we have any score, it's a valid job
        if score > 0:
            return True, min(score, 100.0)  # Cap at 100

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
