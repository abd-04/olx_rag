import streamlit as st
import requests
import os

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OLX Car Finder",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:      #0A0A0F;
    --surface: #13131A;
    --surface2:#1C1C26;
    --border:  #2A2A38;
    --accent:  #6C63FF;
    --accent2: #FF6B6B;
    --green:   #00E5A0;
    --text:    #F0F0FF;
    --muted:   #6B6B8A;
    --card-bg: #16161F;
}

* { box-sizing: border-box; }

.stApp {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 0 2rem !important; max-width: 100% !important; }

/* ── HEADER ── */
.app-header {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 24px;
}

.header-logo {
    width: 40px; height: 40px;
    background: var(--accent);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
}

.header-title {
    font-family: 'Syne', sans-serif;
    font-size: 20px; font-weight: 800;
    color: var(--text); letter-spacing: -0.5px;
}

.header-sub { font-size: 13px; color: var(--muted); }

.header-badge {
    margin-left: auto;
    background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.3);
    color: var(--accent);
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 500;
}

/* ── USER MESSAGE ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 16px;
}

.msg-user-bubble {
    background: var(--accent);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    font-size: 15px;
    line-height: 1.5;
}

/* ── AI MESSAGE ── */
.msg-ai {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-bottom: 16px;
}

.ai-avatar {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}

.msg-ai-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 14px 18px;
    border-radius: 4px 18px 18px 18px;
    max-width: 80%;
    font-size: 15px;
    line-height: 1.7;
}

/* ── FILTER PILLS ── */
.filters-row {
    display: flex; flex-wrap: wrap; gap: 6px;
    margin-top: 10px;
}

.filter-pill {
    background: rgba(108,99,255,0.1);
    border: 1px solid rgba(108,99,255,0.25);
    color: #9B95FF;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 500;
}

/* ── WELCOME ── */
.welcome {
    text-align: center;
    padding: 60px 20px;
}

.welcome-icon { font-size: 52px; margin-bottom: 16px; }

.welcome-title {
    font-family: 'Syne', sans-serif;
    font-size: 26px; font-weight: 800;
    color: var(--text); margin-bottom: 10px;
}

.welcome-sub {
    font-size: 15px; color: var(--muted);
    max-width: 380px; margin: 0 auto 24px;
    line-height: 1.6;
}

.example-chip {
    display: inline-block;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 8px 14px; border-radius: 20px;
    font-size: 13px; margin: 4px;
}

/* ── LISTING CARD ── */
.listing-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
}

.listing-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}

.card-rank {
    font-size: 10px; font-weight: 700;
    color: var(--muted); letter-spacing: 1.5px;
    text-transform: uppercase; margin-bottom: 6px;
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 14px; font-weight: 700;
    color: var(--text); line-height: 1.3;
    margin-bottom: 8px;
}

.card-price {
    font-family: 'Syne', sans-serif;
    font-size: 18px; font-weight: 800;
    color: var(--green); margin-bottom: 10px;
}

.card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px; margin-bottom: 12px;
}

.card-item {
    font-size: 12px; color: var(--muted);
}

.card-link {
    display: block;
    background: rgba(108,99,255,0.1);
    border: 1px solid rgba(108,99,255,0.25);
    color: var(--accent);
    text-align: center;
    padding: 8px; border-radius: 8px;
    font-size: 13px; font-weight: 500;
    text-decoration: none;
}

/* ── PANEL LABEL ── */
.panel-label {
    font-family: 'Syne', sans-serif;
    font-size: 10px; font-weight: 700;
    color: var(--muted); letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
}

/* ── INPUT OVERRIDES ── */
.stTextInput input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    caret-color: var(--accent) !important;
}

.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
}

.stTextInput input::placeholder { color: var(--muted) !important; }

.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 12px 20px !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: #5A52E0 !important;
}

/* divider */
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_listings" not in st.session_state:
    st.session_state.current_listings = []


# ── HELPERS ────────────────────────────────────────────────────────────────────

def ask_backend(question: str):
    try:
        r = requests.post(
            f"{BACKEND_URL}/ask",
            json={"question": question},
            timeout=60
        )
        return r.json()
    except Exception as e:
        return None


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


# ── HEADER ─────────────────────────────────────────────────────────────────────
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

# ── LAYOUT ─────────────────────────────────────────────────────────────────────
col_chat, col_side = st.columns([2.2, 1])

# ── CHAT COLUMN ────────────────────────────────────────────────────────────────
with col_chat:

    # welcome screen
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome">
            <div class="welcome-icon">🚗</div>
            <div class="welcome-title">Find your perfect car or bike</div>
            <div class="welcome-sub">
                Ask anything about used cars and bikes on OLX Pakistan.
                I search real listings to find your best match.
            </div>
            <div>
                <span class="example-chip">family car under 30 lakh</span>
                <span class="example-chip">honda civic lahore</span>
                <span class="example-chip">yamaha ybr good condition</span>
                <span class="example-chip">125cc bike under 2 lakh</span>
                <span class="example-chip">low mileage corolla</span>
                <span class="example-chip">automatic hybrid car</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # render each message
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <div class="msg-user-bubble">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

            else:
                # render AI avatar + bubble separately
                # answer text rendered with st.markdown so it formats correctly
                # no HTML tags will show up this way
                col1, col2 = st.columns([0.06, 0.94])
                with col1:
                    st.markdown("""
                    <div class="ai-avatar">🤖</div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="msg-ai-bubble">
                    """, unsafe_allow_html=True)
                    # render answer as plain markdown — no HTML tags
                    st.markdown(msg["content"])
                    # render filter pills below answer
                    if msg.get("filters"):
                        st.markdown(render_pills(msg["filters"]),
                                    unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # input form
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            user_input = st.text_input(
                "",
                placeholder="Ask about any car... e.g. honda under 25 lakh lahore",
                label_visibility="collapsed"
            )
        with col_btn:
            submitted = st.form_submit_button("Search →")


# ── SIDEBAR COLUMN ─────────────────────────────────────────────────────────────
with col_side:
    if st.session_state.current_listings:
        st.markdown('<div class="panel-label">Top Matches</div>',
                    unsafe_allow_html=True)
        for i, listing in enumerate(st.session_state.current_listings, 1):
            st.markdown(render_card(listing, i), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:50px 0;">
            <div style="font-size:36px; margin-bottom:12px;">🔍</div>
            <div class="panel-label" style="text-align:center">Listings appear here</div>
            <div style="font-size:13px; color:#6B6B8A; margin-top:8px; line-height:1.6">
                Ask a question to see<br>matching car listings
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── HANDLE SUBMIT ──────────────────────────────────────────────────────────────
if submitted and user_input.strip():

    st.session_state.messages.append({
        "role": "user",
        "content": user_input.strip()
    })

    with st.spinner("Searching listings..."):
        result = ask_backend(user_input.strip())

    if result:
        st.session_state.messages.append({
            "role":    "assistant",
            "content": result.get("answer", "Sorry something went wrong."),
            "filters": result.get("filters", {})
        })
        st.session_state.current_listings = result.get("listings", [])
    else:
        st.session_state.messages.append({
            "role":    "assistant",
            "content": "Could not connect to backend. Make sure FastAPI is running on port 8000.",
            "filters": {}
        })

    st.rerun()