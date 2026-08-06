"""
VerifAI — Premium Fact-Verification Platform
Frontend redesigned to feel like a search engine (Google Search / Fact Check
Explorer / Perplexity / Reuters), not an analytics dashboard.

NOTE: This file only changes presentation. All backend calls, search
pipeline, LLM agent, session-state flow, and verification logic are
untouched from the original implementation.
"""

import os
import html as html_lib
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from app_core.search_engine import run_search_pipeline
from app_core.llm_agent import FactCheckerAgent
from app_core.utils import (
    sanitize_claim_input,
    FactCheckReport,
    SearchResult,
    get_domain,
    format_relative_time,
)

# ---------------------------------------------------------------------------
# Bootstrap & Page Config
# ---------------------------------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="VerifAI",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS
_css_path = os.path.join("assets", "style.css")
if os.path.exists(_css_path):
    with open(_css_path) as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# Session state initialization
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "has_searched" not in st.session_state:
    st.session_state.has_searched = False
if "current_results" not in st.session_state:
    st.session_state.current_results = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None

# Read Groq API Key silently from env
groq_key = os.environ.get("GROQ_API_KEY", "")

# ---------------------------------------------------------------------------
# Trending suggestions (with real image thumbnails matching reference UI)
# ---------------------------------------------------------------------------
TRENDING_ITEMS = [
    {
        "img": "https://images.unsplash.com/photo-1517976487492-5750f3195933?w=100&q=80",
        "category": "Science",
        "cat_class": "cat-science",
        "headline": "ISRO successfully launches SSLV-D3 mission",
        "time": "2h ago",
    },
    {
        "img": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=100&q=80",
        "category": "Politics",
        "cat_class": "cat-politics",
        "headline": "Parliament passes new digital data protection bill",
        "time": "3h ago",
    },
    {
        "img": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=100&q=80",
        "category": "Business",
        "cat_class": "cat-business",
        "headline": "Sensex hits all-time high; Nifty closes above 24,500",
        "time": "5h ago",
    },
    {
        "img": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=100&q=80",
        "category": "World",
        "cat_class": "cat-world",
        "headline": "G20 leaders call for global cooperation on AI regulation",
        "time": "6h ago",
    },
    {
        "img": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=100&q=80",
        "category": "World",
        "cat_class": "cat-world",
        "headline": "US Federal Reserve keeps interest rates unchanged",
        "time": "7h ago",
    },
]

# ---------------------------------------------------------------------------
# Pick up a trending-item click (?q=...) before rendering anything else
# ---------------------------------------------------------------------------
_query_param = st.query_params.get("q")
if _query_param and _query_param != st.session_state.search_query:
    st.session_state.search_query = _query_param
    st.session_state.has_searched = True
    st.session_state.current_results = None
    st.session_state.current_report = None
    st.query_params.clear()

# ---------------------------------------------------------------------------
# Animated Placeholder JS & Search Bar Icon Enhancer
# ---------------------------------------------------------------------------
components.html(
    """
    <script>
    // 1. Animated Placeholders
    const placeholders = [
        "Paste a news headline or claim...",
        "Verify a viral message...",
        "Check if this article is true...",
        "Search a fact-checked claim...",
        "Verify a political statement..."
    ];
    let i = 0;
    setInterval(() => {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        inputs.forEach((input) => {
            if (!input.value) {
                input.style.transition = "opacity 200ms ease";
                input.style.opacity = 0.4;
                setTimeout(() => {
                    input.setAttribute("placeholder", placeholders[i % placeholders.length]);
                    input.style.opacity = 1;
                }, 200);
            }
        });
        i++;
    }, 3500);

    // 2. Inject Search Icons dynamically into Streamlit's Input Box
    function injectSearchIcons() {
        const doc = window.parent.document;
        const containers = doc.querySelectorAll('div[data-baseweb="input"]');
        containers.forEach(container => {
            if (!container.querySelector('.search-icon-left')) {
                const leftIcon = doc.createElement('div');
                leftIcon.className = 'search-icon-left';
                leftIcon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
                container.insertBefore(leftIcon, container.firstChild);
            }
            if (!container.querySelector('.search-btn-right')) {
                const rightBtn = doc.createElement('div');
                rightBtn.className = 'search-btn-right';
                rightBtn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
                container.appendChild(rightBtn);
            }
        });
    }

    // 3. Theme Toggle Logic
    (function() {
        const doc = window.parent.document;
        const root = doc.documentElement;
        const stored = window.parent.localStorage.getItem('verifai-theme') || 'light';
        root.setAttribute('data-theme', stored);

        function applyActiveState() {
            const theme = root.getAttribute('data-theme') || 'light';
            const sunBtn = doc.getElementById('verifai-theme-sun');
            const moonBtn = doc.getElementById('verifai-theme-moon');
            if (sunBtn && moonBtn) {
                sunBtn.classList.toggle('active', theme === 'light');
                moonBtn.classList.toggle('active', theme === 'dark');
            }
        }

        function bind() {
            injectSearchIcons();
            const sunBtn = doc.getElementById('verifai-theme-sun');
            const moonBtn = doc.getElementById('verifai-theme-moon');
            if (!sunBtn || !moonBtn || sunBtn.dataset.bound) { return; }
            sunBtn.dataset.bound = "1";
            moonBtn.dataset.bound = "1";
            sunBtn.addEventListener('click', () => {
                root.setAttribute('data-theme', 'light');
                window.parent.localStorage.setItem('verifai-theme', 'light');
                applyActiveState();
            });
            moonBtn.addEventListener('click', () => {
                root.setAttribute('data-theme', 'dark');
                window.parent.localStorage.setItem('verifai-theme', 'dark');
                applyActiveState();
            });
            applyActiveState();
        }

        bind();
        const observer = new MutationObserver(bind);
        observer.observe(doc.body, { childList: true, subtree: true });
    })();
    </script>
    """,
    height=0,
)

# ---------------------------------------------------------------------------
# Shared: Top navigation bar
# ---------------------------------------------------------------------------
NAV_HTML = """
<div class="verifai-nav">
    <a class="nav-logo" href="?" target="_self">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L4 5V11C4 16.5 7.4 21.3 12 22.5C16.6 21.3 20 16.5 20 11V5L12 2Z" fill="#2563EB"/>
            <path d="M9 12L11 14L15.5 9.5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Verif<span class="accent">AI</span>
    </a>
    <div class="nav-links">
        <a class="nav-link" href="#">About</a>
        <a class="nav-link" href="#">How It Works</a>
        <div class="theme-toggle-btn">
            <button id="verifai-theme-sun" title="Light theme" type="button">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="4.5" stroke="currentColor" stroke-width="1.8"/>
                    <path d="M12 2V4.5M12 19.5V22M4.2 4.2L6 6M18 18L19.8 19.8M2 12H4.5M19.5 12H22M4.2 19.8L6 18M18 6L19.8 4.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
            </button>
            <button id="verifai-theme-moon" title="Dark theme" type="button">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                </svg>
            </button>
        </div>
    </div>
</div>
"""
st.markdown(NAV_HTML, unsafe_allow_html=True)


def handle_search():
    st.session_state.has_searched = True
    st.session_state.current_results = None
    st.session_state.current_report = None


def render_trending_section():
    # Use spans instead of divs inside the anchor tags to prevent markdown parsing issues
    rows_html = ""
    for item in TRENDING_ITEMS:
        headline_escaped = html_lib.escape(item["headline"])
        rows_html += f"""
        <a class="trend-row" href="?q={html_lib.escape(item['headline'])}" target="_self">
            <span class="trend-row-inner">
                <img class="trend-thumb" src="{item['img']}" alt="" />
                <span class="trend-body">
                    <span class="trend-category {item['cat_class']}">{item['category']}</span>
                    <span class="trend-headline">{headline_escaped}</span>
                </span>
                <span class="trend-time">{item['time']}</span>
            </span>
        </a>
        """
    st.markdown(
        f"""
        <div class="trending-card">
            <div class="trending-header">
                <div class="trending-title">🔥 Trending Now</div>
                <a class="trending-viewall" href="#">View all ›</a>
            </div>
            {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===================================================================
# Main Application Flow
# ===================================================================

if not st.session_state.has_searched:
    # --- Landing Page Layout ---
    st.markdown(
        '<h1 class="hero-heading">Verify. Trust. Share. <span class="accent">Truth.</span></h1>'
        '<div class="hero-tagline">Search any claim, headline, or statement and get '
        'verified fact-checks from trusted sources.</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search",
        value=st.session_state.search_query,
        key="search_input_landing",
        placeholder="Paste a news headline or claim...",
        label_visibility="collapsed",
        on_change=handle_search,
    )
    st.session_state.search_query = query

    st.markdown(
        '<div class="search-hint"><span class="accent-icon">↗</span> Tip: Try searching a claim or headline to get started</div>',
        unsafe_allow_html=True,
    )

    render_trending_section()

    st.markdown(
        '<div class="footer-note">🛡️ Powered by Google Fact Check</div>',
        unsafe_allow_html=True,
    )

else:
    # --- Results Page Layout ---
    st.markdown(
        '<div class="sticky-search-row">'
        '<a class="sticky-logo" href="?" target="_self">Verif<span class="accent">AI</span></a>'
        '</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search",
        value=st.session_state.search_query,
        key="search_input_results",
        placeholder="Paste a news headline or claim...",
        label_visibility="collapsed",
        on_change=handle_search,
    )
    st.session_state.search_query = query

    cleaned = sanitize_claim_input(st.session_state.search_query)

    if not cleaned:
        st.markdown(
            '<div class="empty-state">'
            '<h2 class="empty-state-title">Invalid Input</h2>'
            '<div class="empty-state-desc">Please enter a clear claim of at least 10 characters to verify.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif not groq_key:
        st.markdown(
            '<div class="empty-state">'
            '<h2 class="empty-state-title">Configuration Error</h2>'
            '<div class="empty-state-desc">Verification key is not configured. Please ensure GROQ_API_KEY is set in `.env`.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        # If we need to fetch results
        if st.session_state.current_results is None:
            loading_placeholder = st.empty()

            def _show_loading(msg):
                loading_placeholder.markdown(
                    f'<div class="skeleton-wrapper">'
                    f'<div class="skeleton-title skeleton-line"></div>'
                    f'<div class="skeleton-line" style="width: 100%;"></div>'
                    f'<div class="skeleton-line" style="width: 100%;"></div>'
                    f'<div class="skeleton-line" style="width: 80%;"></div>'
                    f'<div class="loading-message">{msg}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            _show_loading("Searching across verified fact-check databases...")
            try:
                results, stats = run_search_pipeline(cleaned)
                st.session_state.current_results = results
            except Exception:
                st.session_state.current_results = []

            _show_loading("Analyzing claim context and evidence...")
            try:
                if st.session_state.current_results:
                    agent = FactCheckerAgent(api_key=groq_key)
                    report = agent.evaluate_claim(cleaned, st.session_state.current_results)
                    st.session_state.current_report = report
                else:
                    st.session_state.current_report = FactCheckReport()
            except Exception:
                st.session_state.current_report = FactCheckReport()

            loading_placeholder.empty()

        # Render Results
        results = st.session_state.current_results
        report = st.session_state.current_report
        fc_results = [r for r in results if r.source_api == "factcheck"]

        if not fc_results and not getattr(report, 'professional_fact_checks', None) and getattr(report, 'verdict', 'UNVERIFIABLE') == "UNVERIFIABLE":
            st.markdown(
                '<div class="empty-state">'
                '<h2 class="empty-state-title">No Verified Coverage Found</h2>'
                '<div class="empty-state-desc">'
                'No verified fact-check articles were found for this claim.<br><br>'
                'This does not necessarily mean the claim is true or false — it simply means no '
                'verified review is currently available. Try searching using different keywords '
                'or a more specific claim.'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            v = getattr(report, 'verdict', 'UNVERIFIABLE').upper()
            if v == "TRUE":
                verdict_sentence = '<h3 class="verdict-sentence status-true">According to verified fact-check organizations, this claim is supported by available evidence.</h3>'
            elif v == "FALSE":
                verdict_sentence = '<h3 class="verdict-sentence status-false">According to multiple verified fact-check articles, this claim is false.</h3>'
            elif v in ["PARTLY TRUE", "MISLEADING", "MIXED"]:
                verdict_sentence = '<h3 class="verdict-sentence status-partly">Current fact-check articles indicate that this claim is misleading or missing context.</h3>'
            else:
                verdict_sentence = '<h3 class="verdict-sentence status-unverified">Verified sources do not currently provide sufficient evidence to confirm this claim.</h3>'

            st.markdown(verdict_sentence, unsafe_allow_html=True)

            # Claim box
            st.markdown(
                f'<div class="claim-box">'
                f'<div class="claim-label">Claim</div>'
                f'<div class="claim-text">{html_lib.escape(cleaned)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Summary
            summary = getattr(report, 'summary', '')
            if summary:
                sentences = [s.strip() for s in summary.split('.') if s.strip()]
                short_summary = '. '.join(sentences[:3]) + '.' if sentences else summary
                st.markdown('<div class="section-eyebrow">Summary</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="summary-text">{short_summary}</div>', unsafe_allow_html=True)

            # Supporting Articles (Consolidated HTML output)
            if fc_results:
                fc_html = "<h2>Supporting Articles</h2>"
                for r in fc_results:
                    publisher = r.fact_checker or "Fact Checker"
                    time_str = format_relative_time(r.published_date) if hasattr(r, 'published_date') else ""
                    domain = get_domain(r.url) if hasattr(r, 'url') else ""
                    favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
                    rating = getattr(r, "rating", None) or getattr(r, "textual_rating", None)
                    rating_html = f'<span class="article-rating-pill">{html_lib.escape(str(rating))}</span>' if rating else ""

                    fc_html += (
                        f'<a class="article-card" href="{r.url}" target="_blank" rel="noopener noreferrer">'
                        f'<span class="article-publisher"><img src="{favicon}" width="16" height="16" alt=""> {publisher}</span>'
                        f'<span class="article-title">{r.title}</span>'
                        f'<span class="article-meta-row"><span>{time_str}</span>{rating_html}</span>'
                        f'<span class="article-cta">Read Article →</span>'
                        f'</a>'
                    )
                st.markdown(fc_html, unsafe_allow_html=True)

            # Related News (Consolidated HTML output)
            other_results = [r for r in results if r.source_api != "factcheck"]
            if other_results:
                rn_html = "<h2>Related News</h2>"
                rn_html += '<div class="related-news-note">Additional context from news coverage — not verified fact-checks.</div>'
                for r in other_results:
                    domain = get_domain(r.url) if hasattr(r, 'url') else ""
                    publisher = domain.split('.')[0].capitalize() if domain else "Source"
                    favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
                    time_str = format_relative_time(r.published_date) if getattr(r, "published_date", None) else ""
                    time_html = f'<span class="article-meta-row"><span>{time_str}</span></span>' if time_str else ""

                    rn_html += (
                        f'<a class="article-card news-card" href="{r.url}" target="_blank" rel="noopener noreferrer">'
                        f'<span class="article-publisher"><img src="{favicon}" width="16" height="16" alt=""> {publisher}</span>'
                        f'<span class="article-title">{r.title}</span>'
                        f'{time_html}'
                        f'<span class="article-cta">Open →</span>'
                        f'</a>'
                    )
                st.markdown(rn_html, unsafe_allow_html=True)