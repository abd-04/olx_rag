import streamlit as st
import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 🔥 backend logic imports
from backend.retriever import retrieve
from backend.llm import extract_filters, generate_answer

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="OLX Car Finder",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS (UNCHANGED) ─────────────────────────────────────
st.markdown("""<style>
/* KEEP YOUR FULL CSS HERE (UNCHANGED) */
</style>""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_listings" not in st.session_state:
    st.session_state.current_listings = []

# ── HELPERS (UNCHANGED) ────────────────────────────────────────
def render_card(listing: dict, rank: int):
    ranks = {1:"TOP PICK", 2:"2ND", 3:"3RD", 4:"4TH", 5:"5TH"}
    label = ranks.get(rank, f"#{rank}")
    return f"""
<div class="listing-card">
    <div class="card-rank">{label}</div>
    <div class="card-title">{listing.get('title','—')}</div>
    <div class="card-price">{listing.get('price_lakh','N/A')}</div>
    <div class="card-grid">
        <div class="card-item">📍 {listing.get('city') or '—'}</div>
        <div class="card-item">📅 {listing.get('year') or '—'}</div>
        <div class="card-item">🛣️ {listing.get('km_driven') or '—'} km</div>
        <div class="card-item">⚙️ {listing.get('transmission') or '—'}</div>
        <div class="card-item">⚡ {listing.get('fuel') or '—'}</div>
    </div>
    <a href="{listing.get('url','#')}" target="_blank" class="card-link">
        View on OLX →
    </a>
</div>
"""

def render_pills(filters: dict):
    if not filters:
        return ""
    pills = ""
    for k, v in filters.items():
        if k in ["max_price", "min_price"]:
            v = f"PKR {int(v):,}"
        pills += f'<span class="filter-pill">{v}</span>'
    return f'<div class="filters-row">{pills}</div>'

# ── HEADER ─────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="header-logo">🚗</div>
    <div>
        <div class="header-title">OLX Car Finder</div>
        <div class="header-sub">RAG project for searching cars more conveniently</div>
    </div>
    <div class="header-badge">RAG • Hybrid Search</div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT ─────────────────────────────────────────────────────
col_chat, col_side = st.columns([2.2, 1])

# ── CHAT ───────────────────────────────────────────────────────
with col_chat:

    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome">
            <div class="welcome-icon">🚗</div>
            <div class="welcome-title">Find your perfect car or bike</div>
            <div class="welcome-sub">
                Ask anything about used cars and bikes on OLX Pakistan.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <div class="msg-user-bubble">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

            else:
                col1, col2 = st.columns([0.06, 0.94])
                with col1:
                    st.markdown('<div class="ai-avatar">🤖</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="msg-ai-bubble">', unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    if msg.get("filters"):
                        st.markdown(render_pills(msg["filters"]), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── INPUT ────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([4, 1])

        with col_input:
            user_input = st.text_input(
                "Search",
                placeholder="Ask about any car...",
                label_visibility="collapsed"
            )

        with col_btn:
            submitted = st.form_submit_button("Search →")

# ── SIDEBAR ────────────────────────────────────────────────────
with col_side:
    if st.session_state.current_listings:
        st.markdown('<div class="panel-label">Top Matches</div>', unsafe_allow_html=True)
        for i, listing in enumerate(st.session_state.current_listings, 1):
            st.markdown(render_card(listing, i), unsafe_allow_html=True)
    else:
        st.info("Listings appear here")

# ── MAIN LOGIC (🔥 REPLACED BACKEND) ───────────────────────────
if submitted:
    if not user_input or not user_input.strip():
        st.warning("Please enter a query")
        st.stop()

    question = user_input.strip()

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.spinner("Searching listings..."):

        # 🔥 backend logic here
        filters = extract_filters(question)
        listings = retrieve(question, filters, top_k=5)
        answer = generate_answer(question, listings)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "filters": filters
    })

    st.session_state.current_listings = listings

    st.rerun()