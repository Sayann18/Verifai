"""
Utility functions and shared data structures for the Fact-Checker application.

Provides:
- Dataclasses for unified SearchResult and FactCheckReport
- Trusted/spam domain lists for authority scoring
- Input sanitization, URL normalization, domain extraction
- Authority, relevance, and recency scoring functions
- Credibility star assignment and Trust Score calculations
- Retry-with-backoff decorator for API resilience
- Logging configuration
"""

import re
import logging
import time
import functools
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from urllib.parse import urlparse, urlunparse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fact_checker")


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """Unified search result from any API source."""

    title: str
    url: str
    snippet: str
    source_api: str                          # tavily | newsapi | gnews | factcheck
    published_date: Optional[str] = None
    relevance_score: float = 0.0
    authority_score: float = 0.0
    combined_score: float = 0.0
    claim_rating: Optional[str] = None       # Google Fact Check textual rating
    fact_checker: Optional[str] = None       # Publisher of the fact check


@dataclass
class FactCheckReport:
    """Parsed, structured fact-check report returned by the LLM."""

    verdict: str = "UNVERIFIABLE"
    confidence: int = 0
    summary: str = ""
    detailed_explanation: str = ""
    supporting_evidence: str = ""
    contradicting_evidence: str = ""
    professional_fact_checks: str = ""
    latest_news_summary: str = ""
    sources: str = ""
    raw_response: str = ""


# ---------------------------------------------------------------------------
# Trusted / Spam Domain Lists
# ---------------------------------------------------------------------------

TRUSTED_DOMAINS: set[str] = {
    # Wire services & broadcasters
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "npr.org", "pbs.org", "abc.net.au",
    # Major newspapers
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "wsj.com", "economist.com", "ft.com", "latimes.com",
    "usatoday.com", "thehindu.com", "indianexpress.com",
    "ndtv.com", "timesofindia.indiatimes.com",
    # Science & health
    "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov",
    "who.int", "cdc.gov", "nih.gov",
    # Fact checkers
    "factcheck.org", "politifact.com", "snopes.com",
    "fullfact.org", "altnews.in", "boomlive.in",
    # Government & international
    "nasa.gov", "gov.uk", "whitehouse.gov", "europa.eu",
    "un.org", "unicef.org", "worldbank.org",
}

SPAM_DOMAINS: set[str] = {
    "infowars.com", "naturalnews.com", "beforeitsnews.com",
    "yournewswire.com", "worldnewsdailyreport.com",
    "therightscoop.com", "thegatewaypundit.com",
}


# ---------------------------------------------------------------------------
# Input / URL Helpers
# ---------------------------------------------------------------------------

def sanitize_claim_input(text: str) -> str:
    """Clean and validate user claim input."""
    if not text or not text.strip():
        return ""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) < 10:
        return ""
    if len(cleaned) > 1000:
        cleaned = cleaned[:1000]
    cleaned = re.sub(r"[<>{}\[\]]", "", cleaned)
    return cleaned


def sanitize_url(url: str) -> str:
    """Normalize and validate a URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return ""
        return urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, parsed.query, "",
        ))
    except Exception:
        return ""


def get_domain(url: str) -> str:
    """Extract the bare domain from a URL (strips leading ``www.``)."""
    try:
        domain = urlparse(url).netloc.lower()
        return domain[4:] if domain.startswith("www.") else domain
    except Exception:
        return ""


def normalize_url_for_dedup(url: str) -> str:
    """Return a canonical form of *url* suitable for duplicate detection."""
    try:
        parsed = urlparse(url.lower().rstrip("/"))
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return f"{netloc}{parsed.path.rstrip('/')}"
    except Exception:
        return url.lower().strip()


# ---------------------------------------------------------------------------
# Source Classification & Credibility Rating
# ---------------------------------------------------------------------------

def is_trusted_source(url: str) -> bool:
    """Return ``True`` when *url* belongs to a known trusted outlet."""
    domain = get_domain(url)
    return any(domain == t or domain.endswith("." + t) for t in TRUSTED_DOMAINS)


def is_spam_source(url: str) -> bool:
    """Return ``True`` when *url* belongs to a known spam / disinformation site."""
    domain = get_domain(url)
    return any(domain == s or domain.endswith("." + s) for s in SPAM_DOMAINS)


def get_credibility_stars(url: str) -> tuple[str, int]:
    """Return (star_string, numeric_rating) based on domain authority."""
    domain = get_domain(url)
    if is_spam_source(url):
        return ("★☆☆☆☆", 1)
    
    five_star = {
        "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "who.int",
        "cdc.gov", "nih.gov", "nasa.gov", "nature.com", "science.org",
        "factcheck.org", "politifact.com", "snopes.com", "fullfact.org",
        "gov.uk", "whitehouse.gov", "europa.eu", "un.org"
    }
    if any(domain == d or domain.endswith("." + d) or domain.endswith(".gov") for d in five_star):
        return ("★★★★★", 5)
    
    four_star = {
        "nytimes.com", "washingtonpost.com", "theguardian.com", "wsj.com",
        "economist.com", "ft.com", "latimes.com", "usatoday.com", "thehindu.com",
        "indianexpress.com", "ndtv.com", "timesofindia.indiatimes.com",
        "npr.org", "pbs.org", "abc.net.au"
    }
    if any(domain == d or domain.endswith("." + d) or domain.endswith(".edu") or domain.endswith(".org") for d in four_star):
        return ("★★★★☆", 4)
    
    if "wikipedia.org" in domain or "medium.com" in domain:
        return ("★★★☆☆", 3)
    
    if is_trusted_source(url):
        return ("★★★★☆", 4)
    
    return ("★★★☆☆", 3)


# ---------------------------------------------------------------------------
# Trust Score & Rating Logic
# ---------------------------------------------------------------------------

def calculate_trust_score(verdict: str, confidence: int) -> tuple[int, str, str, str]:
    """Calculate Trust Score (0-100%), status text, color, and status chip label.
    
    Color scale:
      0-30: Red (#EF4444)
      31-60: Orange (#F59E0B)
      61-80: Blue (#2563EB)
      81-100: Green (#22C55E)
    """
    v = verdict.upper().strip()
    c = max(0, min(100, confidence))
    
    if v == "TRUE":
        score = max(75, c)
    elif v == "FALSE":
        score = min(25, max(5, 100 - c))
    elif v == "MISLEADING":
        score = 45
    elif v == "MIXED":
        score = 55
    else:  # UNVERIFIABLE
        score = max(20, c // 2)
        
    if score >= 81:
        color = "#22C55E"
        status = "Highly Reliable"
        chip = "✅ Highly Reliable"
    elif score >= 61:
        color = "#2563EB"
        status = "Reliable"
        chip = "🟢 Reliable"
    elif score >= 41:
        color = "#F59E0B"
        status = "Partially Reliable"
        chip = "🟡 Partially Reliable"
    elif score >= 21:
        color = "#F59E0B"
        status = "Questionable"
        chip = "🟠 Questionable"
    else:
        color = "#EF4444"
        status = "Likely False"
        chip = "🔴 Likely False"
        
    if v == "UNVERIFIABLE" and score < 40:
        chip = "⚪ Insufficient Evidence"
        status = "Insufficient Evidence"
        color = "#6B7280"
        
    return score, status, color, chip


# ---------------------------------------------------------------------------
# Scoring Functions
# ---------------------------------------------------------------------------

def compute_authority_score(url: str) -> float:
    """Heuristic authority score for a URL (0.0 – 1.0)."""
    if is_spam_source(url):
        return 0.0
    if is_trusted_source(url):
        return 1.0
    domain = get_domain(url)
    if domain.endswith(".gov") or domain.endswith(".edu"):
        return 0.9
    if domain.endswith(".org"):
        return 0.7
    return 0.5


def compute_relevance_score(claim: str, title: str, snippet: str) -> float:
    """Keyword-overlap relevance score between claim and result text (0.0 – 1.0)."""
    claim_words = set(re.findall(r"\b\w{3,}\b", claim.lower()))
    if not claim_words:
        return 0.0
    text_words = set(re.findall(r"\b\w{3,}\b", f"{title} {snippet}".lower()))
    if not text_words:
        return 0.0
    return len(claim_words & text_words) / len(claim_words)


def compute_recency_score(published_date: Optional[str]) -> float:
    """Recency score (0.0 – 1.0).  More recent → higher score."""
    if not published_date:
        return 0.3
    try:
        dt = _parse_date(published_date)
        if dt is None:
            return 0.3
        age_hours = (datetime.now(timezone.utc).replace(tzinfo=None) - dt).total_seconds() / 3600
        if age_hours < 24:
            return 1.0
        if age_hours < 72:
            return 0.9
        if age_hours < 168:
            return 0.8
        if age_hours < 720:
            return 0.6
        return 0.4
    except Exception:
        return 0.3


def _parse_date(date_str: str) -> Optional[datetime]:
    """Try common ISO-ish date formats and return a naive UTC datetime."""
    truncated = date_str[:19]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(truncated, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

def format_relative_time(date_str: Optional[str]) -> str:
    """Convert an ISO date string to a human-readable relative timestamp."""
    if not date_str:
        return "Recent"
    try:
        dt = _parse_date(date_str)
        if dt is None:
            return date_str[:10] if len(date_str) >= 10 else date_str
        diff = datetime.now(timezone.utc).replace(tzinfo=None) - dt
        if diff.days == 0:
            hours = diff.seconds // 3600
            return f"{diff.seconds // 60}m ago" if hours == 0 else f"{hours}h ago"
        if diff.days == 1:
            return "Yesterday"
        if diff.days < 7:
            return f"{diff.days}d ago"
        if diff.days < 30:
            return f"{diff.days // 7}w ago"
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else date_str


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator: retry the wrapped function with exponential back-off."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
            return None
        return wrapper
    return decorator