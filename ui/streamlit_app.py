"""
Streamlit UI — Verified Health Content Recommender
Educational content only. Not medical advice.
"""

import streamlit as st
import httpx
import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Verified Health Content",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom styling ──────────────────────────────────────────
st.markdown("""
<style>
    .disclaimer-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border-left: 5px solid #ffc107;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 0.9em;
        color: #856404;
    }
    .trust-badge-org {
        background: #d4edda;
        color: #155724;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .trust-badge-creator {
        background: #cce5ff;
        color: #004085;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .urgency-emergency {
        background: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 16px;
        border-radius: 6px;
    }
    .urgency-soon {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 16px;
        border-radius: 6px;
    }
    .urgency-routine {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 16px;
        border-radius: 6px;
    }

    .qa-answer-box {
        background: #1e293b;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 8px 0;
        color: #e2e8f0 !important;
        line-height: 1.6;
    }
    .explain-box {
        background: #1e293b;
        border-left: 4px solid #06b6d4;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 8px 0;
        color: #e2e8f0 !important;
        line-height: 1.6;
    }
    .related-topic-chip {
        display: inline-block;
        background: #1e3a5f;
        color: #93c5fd !important;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        margin: 2px 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# All available topics
ALL_TOPICS = [
    # Core
    "heart-health", "diabetes", "respiratory", "mental-health",
    "nutrition", "exercise-fitness", "sleep", "skin-conditions",
    "digestive-health", "thyroid", "bone-joint", "allergies",
    "eye-health", "ear-nose-throat", "dental-health",
    "womens-health", "mens-health", "child-health", "senior-health",
    "pregnancy", "immunization", "infectious-disease",
    "cancer-awareness", "chronic-pain", "first-aid", "general-wellness",
    # Injuries
    "sports-injuries", "fractures-sprains", "burns-wounds", "head-injury",
    # Organ/System
    "kidney-disease", "liver-disease", "blood-disorders",
    "neurological", "urological-health",
    # Niche
    "autoimmune", "rare-diseases", "genetic-conditions",
    "endocrine-disorders", "tropical-diseases", "poisoning-toxicology",
]


@st.cache_data(ttl=120, show_spinner=False)
def _cached_api_get(path: str, params_key: str = ""):
    """Cached GET request. params_key is used for cache key only."""
    import json as _json
    params = _json.loads(params_key) if params_key else None
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def api_get(path: str, params: dict = None):
    """Make a cached GET request to the backend API."""
    import json as _json
    params_key = _json.dumps(params, sort_keys=True) if params else ""
    result = _cached_api_get(path, params_key)
    if result is None:
        st.error("Could not reach the API or request timed out. Is the backend running?")
    return result


def api_post(path: str, data: dict = None):
    """Make a POST request to the backend API."""
    try:
        r = httpx.post(f"{API_BASE}{path}", json=data, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def show_disclaimer():
    """Show the mandatory disclaimer."""
    st.markdown(
        '<div class="disclaimer-box">⚠️ <b>Educational content only.</b> '
        'Not medical advice. If worried, seek professional care.</div>',
        unsafe_allow_html=True,
    )


# ── Helper: Q&A and Explain UI ──────────────────────────────

def _render_qa_and_explain(item_id: int, item: dict):
    """Render the Q&A and explain UI for a content item."""
    tab_qa, tab_explain, tab_related = st.tabs(["❓ Ask a Question", "📖 Reading Level", "🔗 Related Topics"])

    with tab_qa:
        question = st.text_input(
            "Ask about this article:",
            placeholder="e.g., What are the main risk factors mentioned?",
            key=f"qa_input_{item_id}",
        )
        if st.button("Ask", key=f"qa_btn_{item_id}") and question:
            with st.spinner("Finding answer in the article..."):
                result = api_post(f"/content/{item_id}/ask", {"question": question})
                if result:
                    st.markdown(
                        f'<div class="qa-answer-box">{result.get("answer", "No answer available.")}</div>',
                        unsafe_allow_html=True,
                    )
                    if result.get("grounded"):
                        st.caption(f"✅ Answer grounded in: {result.get('source_title', 'source article')}")
                    else:
                        st.caption("⚠️ This question may not be fully covered by the article.")
                    st.caption(result.get("disclaimer", ""))

    with tab_explain:
        level = st.radio(
            "Choose reading level:",
            ["simple", "standard", "detailed"],
            index=1,
            horizontal=True,
            key=f"level_{item_id}",
            help="Simple: plain language for kids/teens · Standard: general adult · Detailed: in-depth with medical terms",
        )
        if st.button("Explain at this level", key=f"explain_btn_{item_id}"):
            with st.spinner(f"Rewriting at {level} level..."):
                result = api_get(f"/content/{item_id}/explain", {"level": level})
                if result:
                    st.markdown(
                        f'<div class="explain-box">{result.get("explanation", "")}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(result.get("disclaimer", ""))

    with tab_related:
        if st.button("Load related topics", key=f"related_btn_{item_id}"):
            with st.spinner("Finding related topics..."):
                detail = api_get(f"/content/{item_id}")
                if detail:
                    related = detail.get("related_topics", [])
                    if related:
                        st.markdown("**You might also want to explore:**")
                        for rt in related:
                            st.markdown(
                                f'<span class="related-topic-chip">🔗 {rt.get("topic", "")}</span> '
                                f'— {rt.get("reason", "")}',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No related topic suggestions available. LLM may be unavailable.")


# ── Sidebar navigation ─────────────────────────────────────
st.sidebar.title("🏥 Verified Health")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📰 Verified Feed", "💬 Assistant (RAG)", "📄 Prescription Scanner", "🚨 Seek Care Guidance"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption("Educational content only. Not medical advice.")

# ── Page: Verified Feed ─────────────────────────────────────
if page == "📰 Verified Feed":
    st.title("📰 Verified Health Content Feed")
    show_disclaimer()

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search by symptom or condition", placeholder="e.g., chest pain, headache, fatigue, diabetes, sugar problems")
    with col2:
        topic_filter = st.selectbox("Topic", [""] + ALL_TOPICS)
    with col3:
        type_filter = st.selectbox("Type", ["", "article", "video", "short-form"])
    with col4:
        result_limit = st.slider("Result Limit", min_value=1, max_value=50, value=5, step=1)

    # Fetch content
    params = {"limit": result_limit}
    if search_query:
        params["q"] = search_query
    if topic_filter:
        params["topic"] = topic_filter
    if type_filter:
        params["content_type"] = type_filter

    result = api_get("/content/search", params=params)

    if result:
        items = result.get("items", [])
        st.markdown(f"**{result.get('total', 0)} results found**")

        if not items:
            st.info("No content found. Try a different search or run the ingestion pipeline first.")

        for item in items:
            from ui.components.cards import render_content_card
            render_content_card(item)

            # ── Q&A and Explain section for each item ──
            item_id = item.get("id")
            if item_id:
                with st.expander("🤖 Ask about this article / Adjust reading level"):
                    _render_qa_and_explain(item_id, item)


# ── Page: Seek Care Guidance ────────────────────────────────
elif page == "🚨 Seek Care Guidance":
    st.title("🚨 Seek Care Guidance")
    show_disclaimer()

    st.markdown(
        "**This tool helps you think about whether to seek professional care.** "
        "It does NOT provide diagnosis or medical advice. Answer the questions "
        "below and the tool will suggest a general urgency level based on "
        "trusted public health guidelines."
    )

    from ui.components.triage import render_triage_page
    render_triage_page(api_get, api_post)

# ── Page: Assistant (RAG) ────────────────────────────────
elif page == "💬 Assistant (RAG)":
    from ui.components.chat import render_chat_page
    render_chat_page(api_post)

# ── Page: Prescription Scanner ────────────────────────────────
elif page == "📄 Prescription Scanner":
    from ui.components.scanner import render_scanner_page
    render_scanner_page(api_post)



