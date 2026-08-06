"""
Multi-source search engine with concurrent API calls, deduplication, and
evidence ranking.

Pipeline:
    1. search_tavily()          — deep web search
    2. search_newsapi()         — recent news articles
    3. search_gnews()           — additional news coverage
    4. search_google_factcheck()— professional fact-check claims
    5. merge_search_results()   — combine all results
    6. remove_duplicates()      — deduplicate by normalised URL
    7. rank_evidence()          — score by relevance + authority + recency
    8. format_context_for_llm() — build structured prompt context

All four API calls execute concurrently via ThreadPoolExecutor.
Each function handles timeouts, rate limits, invalid keys, empty responses,
and network failures gracefully — the application never crashes.
"""

import os
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable

from app_core.utils import (
    SearchResult,
    retry_with_backoff,
    sanitize_url,
    is_spam_source,
    compute_authority_score,
    compute_relevance_score,
    compute_recency_score,
    normalize_url_for_dedup,
)

logger = logging.getLogger("fact_checker.search")

# Timeout applied to every outbound HTTP request (seconds).
API_TIMEOUT: int = 12


# ===================================================================
# Individual Search Functions
# ===================================================================

@retry_with_backoff(max_retries=2, base_delay=1.0, exceptions=(requests.RequestException, ValueError))
def search_tavily(claim: str, max_results: int = 5) -> list[SearchResult]:
    """Deep web search via the Tavily Search API.

    Returns up to *max_results* :class:`SearchResult` objects.
    Gracefully returns an empty list on failure.
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set — skipping Tavily search")
        return []

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": f"fact check: {claim}",
                "max_results": max_results,
                "include_answer": False,
                "search_depth": "advanced",
            },
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[SearchResult] = []
        for item in data.get("results", []):
            url = sanitize_url(item.get("url", ""))
            if not url or is_spam_source(url):
                continue
            results.append(SearchResult(
                title=item.get("title", "Untitled"),
                url=url,
                snippet=(item.get("content", "") or "")[:500],
                source_api="tavily",
                published_date=item.get("published_date"),
                relevance_score=float(item.get("score", 0.0)),
            ))
        logger.info("Tavily returned %d results", len(results))
        return results

    except requests.exceptions.HTTPError as exc:
        _log_http_error("Tavily", exc)
        raise
    except requests.exceptions.Timeout:
        logger.error("Tavily API: request timed out")
        raise
    except Exception as exc:
        logger.error("Tavily API unexpected error: %s", exc)
        return []


@retry_with_backoff(max_retries=2, base_delay=1.0, exceptions=(requests.RequestException,))
def search_newsapi(claim: str, max_results: int = 5) -> list[SearchResult]:
    """Search recent news articles via NewsAPI ``/v2/everything``."""
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        logger.warning("NEWS_API_KEY not set — skipping NewsAPI search")
        return []

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": claim,
                "sortBy": "relevancy",
                "pageSize": max_results,
                "language": "en",
                "apiKey": api_key,
            },
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "ok":
            logger.warning("NewsAPI returned status=%s", data.get("status"))
            return []

        results: list[SearchResult] = []
        for article in data.get("articles", []):
            url = sanitize_url(article.get("url", ""))
            if not url or is_spam_source(url):
                continue
            snippet = (
                article.get("description")
                or (article.get("content") or "")[:500]
                or ""
            )
            results.append(SearchResult(
                title=article.get("title", "Untitled"),
                url=url,
                snippet=snippet,
                source_api="newsapi",
                published_date=article.get("publishedAt"),
            ))
        logger.info("NewsAPI returned %d results", len(results))
        return results

    except requests.exceptions.HTTPError as exc:
        _log_http_error("NewsAPI", exc)
        raise
    except requests.exceptions.Timeout:
        logger.error("NewsAPI: request timed out")
        raise
    except Exception as exc:
        logger.error("NewsAPI unexpected error: %s", exc)
        return []


@retry_with_backoff(max_retries=2, base_delay=1.0, exceptions=(requests.RequestException,))
def search_gnews(claim: str, max_results: int = 5) -> list[SearchResult]:
    """Search additional news coverage via the GNews API."""
    api_key = os.environ.get("GNEWS_API_KEY", "")
    if not api_key:
        logger.warning("GNEWS_API_KEY not set — skipping GNews search")
        return []

    try:
        resp = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": claim,
                "max": max_results,
                "lang": "en",
                "sortby": "relevance",
                "apikey": api_key,
            },
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[SearchResult] = []
        for article in data.get("articles", []):
            url = sanitize_url(article.get("url", ""))
            if not url or is_spam_source(url):
                continue
            snippet = (
                article.get("description")
                or (article.get("content") or "")[:500]
                or ""
            )
            results.append(SearchResult(
                title=article.get("title", "Untitled"),
                url=url,
                snippet=snippet,
                source_api="gnews",
                published_date=article.get("publishedAt"),
            ))
        logger.info("GNews returned %d results", len(results))
        return results

    except requests.exceptions.HTTPError as exc:
        _log_http_error("GNews", exc)
        raise
    except requests.exceptions.Timeout:
        logger.error("GNews API: request timed out")
        raise
    except Exception as exc:
        logger.error("GNews API unexpected error: %s", exc)
        return []


@retry_with_backoff(max_retries=2, base_delay=1.0, exceptions=(requests.RequestException,))
def search_google_factcheck(claim: str, max_results: int = 5) -> list[SearchResult]:
    """Search professional fact-check claims via Google Fact Check Tools API."""
    api_key = os.environ.get("GOOGLE_FACTCHECK_API_KEY", "")
    if not api_key:
        logger.warning("GOOGLE_FACTCHECK_API_KEY not set — skipping Google Fact Check")
        return []

    try:
        resp = requests.get(
            "https://factchecktools.googleapis.com/v1alpha1/claims:search",
            params={
                "query": claim,
                "pageSize": max_results,
                "key": api_key,
            },
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[SearchResult] = []
        for claim_obj in data.get("claims", []):
            for review in claim_obj.get("claimReview", []):
                url = sanitize_url(review.get("url", ""))
                if not url:
                    continue
                publisher = review.get("publisher", {}).get("name", "Unknown")
                rating = review.get("textualRating", "")
                title = review.get("title", "") or claim_obj.get("text", "Untitled")
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=(
                        f"Rating: {rating}. Reviewed by: {publisher}. "
                        f"Claim: {claim_obj.get('text', '')}"
                    ),
                    source_api="factcheck",
                    published_date=review.get("reviewDate"),
                    claim_rating=rating,
                    fact_checker=publisher,
                    authority_score=1.0,  # professional fact checks → max authority
                ))
        logger.info("Google Fact Check returned %d results", len(results))
        return results

    except requests.exceptions.HTTPError as exc:
        _log_http_error("Google Fact Check", exc)
        raise
    except requests.exceptions.Timeout:
        logger.error("Google Fact Check API: request timed out")
        raise
    except Exception as exc:
        logger.error("Google Fact Check API unexpected error: %s", exc)
        return []


# ===================================================================
# Pipeline Functions
# ===================================================================

def merge_search_results(*result_lists: list[SearchResult]) -> list[SearchResult]:
    """Merge results from multiple APIs into a single flat list."""
    merged: list[SearchResult] = []
    for results in result_lists:
        if results:
            merged.extend(results)
    return merged


def remove_duplicates(results: list[SearchResult]) -> list[SearchResult]:
    """De-duplicate results by normalised URL."""
    seen: set[str] = set()
    unique: list[SearchResult] = []
    for r in results:
        key = normalize_url_for_dedup(r.url)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    removed = len(results) - len(unique)
    if removed:
        logger.info("Removed %d duplicate results", removed)
    return unique


def rank_evidence(results: list[SearchResult], claim: str) -> list[SearchResult]:
    """Score and sort results by weighted combination of relevance, authority, and recency."""
    for r in results:
        if r.authority_score == 0.0:
            r.authority_score = compute_authority_score(r.url)
        relevance = compute_relevance_score(claim, r.title, r.snippet)
        r.relevance_score = max(r.relevance_score, relevance)
        recency = compute_recency_score(r.published_date)
        r.combined_score = (
            0.35 * r.relevance_score
            + 0.35 * r.authority_score
            + 0.30 * recency
        )
    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results


def format_context_for_llm(results: list[SearchResult]) -> str:
    """Format ranked results into a structured text block for the LLM prompt."""
    if not results:
        return "No relevant evidence was found from any source."

    buckets: dict[str, list[SearchResult]] = {
        "factcheck": [], "tavily": [], "newsapi": [], "gnews": [],
    }
    for r in results:
        buckets.setdefault(r.source_api, []).append(r)

    parts: list[str] = []

    # Professional fact checks first (highest priority)
    if buckets["factcheck"]:
        parts.append("=== PROFESSIONAL FACT CHECKS ===")
        for i, r in enumerate(buckets["factcheck"], 1):
            parts.append(
                f"[Fact Check {i}]\n"
                f"Title: {r.title}\n"
                f"Rating: {r.claim_rating or 'N/A'}\n"
                f"Checked by: {r.fact_checker or 'Unknown'}\n"
                f"URL: {r.url}\n"
                f"Details: {r.snippet}"
            )

    # Tavily web evidence
    if buckets["tavily"]:
        parts.append("\n=== WEB EVIDENCE (Tavily) ===")
        for i, r in enumerate(buckets["tavily"], 1):
            parts.append(
                f"[Source {i}] (Authority: {r.authority_score:.1f}, "
                f"Relevance: {r.relevance_score:.1f})\n"
                f"Title: {r.title}\n"
                f"URL: {r.url}\n"
                f"Content: {r.snippet}"
            )

    # News articles (NewsAPI + GNews combined)
    news = buckets["newsapi"] + buckets["gnews"]
    if news:
        parts.append("\n=== LATEST NEWS ARTICLES ===")
        for i, r in enumerate(news, 1):
            parts.append(
                f"[News {i}] (Source API: {r.source_api.upper()}, "
                f"Published: {r.published_date or 'Unknown'})\n"
                f"Title: {r.title}\n"
                f"URL: {r.url}\n"
                f"Summary: {r.snippet}"
            )

    return "\n\n".join(parts)


# ===================================================================
# Orchestrator
# ===================================================================

def run_search_pipeline(
    claim: str,
    progress_callback: Optional[Callable] = None,
) -> tuple[list[SearchResult], dict]:
    """Execute the full search pipeline with concurrent API calls.

    Args:
        claim: The user's claim to verify.
        progress_callback: Optional ``fn(api_name, count, error=None)``
            invoked as each API finishes.

    Returns:
        ``(ranked_results, pipeline_stats)`` where *pipeline_stats* is a dict
        with per-API counts, total count, duplicates removed, and error list.
    """
    stats: dict = {
        "tavily": 0,
        "newsapi": 0,
        "gnews": 0,
        "factcheck": 0,
        "total": 0,
        "duplicates_removed": 0,
        "errors": [],
    }

    tasks = {
        "tavily":    (search_tavily, claim),
        "newsapi":   (search_newsapi, claim),
        "gnews":     (search_gnews, claim),
        "factcheck": (search_google_factcheck, claim),
    }

    api_results: dict[str, list[SearchResult]] = {}

    with ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {
            pool.submit(fn, q): name for name, (fn, q) in tasks.items()
        }
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                res = future.result(timeout=20) or []
                api_results[name] = res
                stats[name] = len(res)
                if progress_callback:
                    progress_callback(name, len(res))
            except Exception as exc:
                logger.error("Pipeline — %s failed: %s", name, exc)
                api_results[name] = []
                stats["errors"].append(f"{name}: {exc}")
                if progress_callback:
                    progress_callback(name, 0, error=str(exc))

    # Merge → de-duplicate → rank
    merged = merge_search_results(*api_results.values())
    before = len(merged)
    unique = remove_duplicates(merged)
    stats["duplicates_removed"] = before - len(unique)

    ranked = rank_evidence(unique, claim)
    stats["total"] = len(ranked)

    return ranked, stats


# ===================================================================
# Helpers (private)
# ===================================================================

def _log_http_error(api_name: str, exc: requests.exceptions.HTTPError) -> None:
    """Log a human-readable message for common HTTP error codes."""
    if exc.response is not None:
        code = exc.response.status_code
        if code == 401:
            logger.error("%s API: invalid API key (401)", api_name)
        elif code == 429:
            logger.error("%s API: rate limit exceeded (429)", api_name)
        else:
            logger.error("%s API: HTTP %d — %s", api_name, code, exc)
    else:
        logger.error("%s API: HTTP error (no response) — %s", api_name, exc)