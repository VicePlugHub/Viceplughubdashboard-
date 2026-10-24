"""
VicePlug Hub // GTA VI Intelligence & Content Operations
Pixel-perfect recreation of Designer (2).png for Streamlit Community Cloud
"""

import os
import json
import base64
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Optional integrations with graceful fallbacks
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# --------------------------------------------------
# STREAMLIT CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug Hub // GTA VI Content Intelligence",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# AUTO-LOAD OR EXTRACT ASSETS FROM MOCKUP
# --------------------------------------------------
def get_asset_base64(filename: str) -> str:
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

# Try extracting from Designer (2).png if present
if os.path.exists("Designer (2).png") and not os.path.exists("hero_bg.jpg"):
    try:
        import cv2
        img = cv2.imread("Designer (2).png")
        if img is not None:
            cv2.imwrite("hero_bg.jpg", img[0:560, :], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            cv2.imwrite("st1.jpg", img[715:755, 325:380], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            cv2.imwrite("st2.jpg", img[768:808, 325:380], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            cv2.imwrite("st3.jpg", img[823:863, 325:380], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            cv2.imwrite("st4.jpg", img[877:917, 325:380], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            cv2.imwrite("video_thumb_perfect.jpg", img[746:818, 975:1195], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    except Exception:
        pass

b64_hero = get_asset_base64("hero_bg.jpg")
b64_st1 = get_asset_base64("st1.jpg")
b64_st2 = get_asset_base64("st2.jpg")
b64_st3 = get_asset_base64("st3.jpg")
b64_st4 = get_asset_base64("st4.jpg")
b64_vt = get_asset_base64("video_thumb_perfect.jpg")

# --------------------------------------------------
# DESIGN SYSTEM & STYLING (MATCHING MOCKUP EXACTLY)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-dark: #060913;
    --cc-bg: #090E1B;
    --card-surface: #0E1528;
    --card-border: #1E293B;
    --pink-neon: #FF2E93;
    --pink-bright: #FF007A;
    --purple-glow: #A855F7;
    --cyan-glow: #00F5FF;
    --emerald-glow: #10B981;
    --amber-glow: #F59E0B;
    --text-main: #FFFFFF;
    --text-muted: #8E9FB8;
    --text-dim: #64748B;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-main);
    background-color: var(--bg-dark);
}

.stApp {
    background-color: var(--bg-dark);
}

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    max-width: 1680px;
    padding-top: 0.5rem;
    padding-bottom: 2rem;
}

/* Hero Section */
.hero-wrapper {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 24px;
    background-color: #0c1222;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-image-banner {
    width: 100%;
    display: block;
    border-radius: 16px;
}

/* Command Center Frame */
.command-center-frame {
    background: #080D1A;
    border: 1.5px solid rgba(168, 85, 247, 0.45);
    border-radius: 18px;
    box-shadow: 0 0 35px rgba(168, 85, 247, 0.2), inset 0 0 20px rgba(0, 0, 0, 0.6);
    padding: 20px 22px;
    position: relative;
}

/* Sidebar Nav Items */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 1.25rem;
    color: #FFF;
    margin-bottom: 20px;
    letter-spacing: -0.02em;
}

.sidebar-logo span {
    color: var(--pink-neon);
}

div[data-testid="stVerticalBlock"] .stButton > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #8E9FB8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    text-align: left !important;
    padding: 8px 12px !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stVerticalBlock"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #FFFFFF !important;
}

/* Active Nav Button */
.nav-btn-active > button {
    background: linear-gradient(90deg, rgba(255, 46, 147, 0.2) 0%, rgba(255, 46, 147, 0.04) 100%) !important;
    border: 1px solid rgba(255, 46, 147, 0.45) !important;
    border-left: 3px solid var(--pink-neon) !important;
    color: #FFFFFF !important;
}

/* Metric Card */
.metric-card-box {
    background: #0E1528;
    border: 1px solid #1C263D;
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 10px;
}

.metric-icon-circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
}

.metric-label-text {
    font-size: 0.76rem;
    color: var(--text-muted);
    font-weight: 500;
}

.metric-val-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-top: 10px;
}

.metric-number-big {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.85rem;
    font-weight: 700;
    color: #FFF;
    line-height: 1;
}

/* Middle Panels */
.panel-box {
    background: #0C1324;
    border: 1px solid #1B253B;
    border-radius: 12px;
    padding: 16px;
    height: 100%;
}

.panel-header-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.96rem;
    font-weight: 700;
    color: #FFF;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

/* Story Item */
.story-row-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.story-row-item:last-child {
    border-bottom: none;
}

.story-index-num {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #64748B;
    width: 14px;
}

.story-thumb-img {
    width: 48px;
    height: 34px;
    border-radius: 6px;
    object-fit: cover;
    background: #1E293B;
}

.story-score-pill {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--pink-neon);
    background: rgba(255, 46, 147, 0.1);
    border: 1px solid rgba(255, 46, 147, 0.35);
    padding: 3px 8px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}

/* Bottom Ticker */
.bottom-ticker-bar {
    background: rgba(9, 14, 27, 0.9);
    border: 1px solid rgba(168, 85, 247, 0.4);
    border-radius: 12px;
    padding: 10px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 18px;
    font-size: 0.78rem;
}

.live-pill {
    background: #EF4444;
    color: #FFF;
    font-weight: 800;
    font-size: 0.68rem;
    padding: 2px 7px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0% { opacity: 0.8; transform: scale(0.98); }
    50% { opacity: 1; transform: scale(1.02); }
    100% { opacity: 0.8; transform: scale(0.98); }
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# APP STATE
# --------------------------------------------------
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Dashboard"

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""


# --------------------------------------------------
# TOP SECTION: HERO SHOWCASE (FROM MOCKUP)
# --------------------------------------------------
if b64_hero:
    st.markdown(f"""
        <div class="hero-wrapper">
            <img src="data:image/jpeg;base64,{b64_hero}" class="hero-image-banner" alt="GTA VI Hero Showcase" />
        </div>
    """, unsafe_allow_html=True)
else:
    # CSS fallback if image is not present
    st.markdown("""
        <div class="hero-wrapper" style="padding: 40px; background: linear-gradient(135deg, #10172B 0%, #30103A 60%, #520F38 100%);">
            <div style="font-size:0.75rem; color:#8E9FB8; font-weight:700; letter-spacing:0.15em;">VICE CITY LIVES ONLINE.</div>
            <div style="font-family:'Space Grotesk'; font-size:2.8rem; font-weight:800; line-height:1.1; margin:8px 0 12px 0;">
                GTA VI RESEARCH.<br>
                <span style="color:#FF2E93;">AI INTELLIGENCE.</span><br>
                VIRAL CONTENT.
            </div>
            <p style="color:#8E9FB8; font-size:0.95rem; max-width:650px; margin-bottom:20px;">
                Track breaking GTA VI news, discover trending videos, identify viral opportunities with AI, and generate ready-to-publish hooks, scripts, captions, and hashtags from one command center.
            </p>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# THE COMMAND CENTER CONTAINER (MATCHING MOCKUP)
# --------------------------------------------------
st.markdown('<div class="command-center-frame">', unsafe_allow_html=True)

col_sidebar, col_content = st.columns([1.1, 5.2], gap="medium")

# ==================================================
# LEFT SIDEBAR NAVIGATION
# ==================================================
with col_sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <span>👑</span> VICE<span>PLUG</span> HUB
        </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("Dashboard", "🏠"),
        ("Research Feed", "📰"),
        ("Viral Opportunities", "🎯"),
        ("Video Discovery", "🎥"),
        ("AI Studio", "🧠"),
        ("Script Generator", "📝"),
        ("Content Pipeline", "⚡"),
        ("Review Queue", "☑️"),
        ("Google Sheets Sync", "📊"),
        ("Settings", "⚙️"),
    ]

    for label, icon in nav_items:
        is_active = st.session_state["active_tab"] == label
        btn_key = f"nav_{label}"
        if is_active:
            st.markdown('<div class="nav-btn-active">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=btn_key, use_container_width=True):
                st.session_state["active_tab"] = label
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {label}", key=btn_key, use_container_width=True):
                st.session_state["active_tab"] = label
                st.rerun()

    st.markdown("""
        <div style="margin-top: 40px; font-size: 0.68rem; color: #64748B; font-weight: 600; letter-spacing: 0.08em; line-height: 1.4;">
            GOOD CONTENT<br>BUILDS BIGGER WORLDS.
        </div>
    """, unsafe_allow_html=True)


# ==================================================
# MAIN COMMAND CENTER AREA
# ==================================================
with col_content:

    # 1. Header Bar: Greeting + Search + Avatar
    head_left, head_right = st.columns([1.8, 1.4])
    with head_left:
        st.markdown("""
            <div>
                <div style="font-family:'Space Grotesk'; font-size:1.6rem; font-weight:700; color:#FFF; line-height:1.2;">
                    Welcome back, Creator.
                </div>
                <div style="font-size:0.85rem; color:#8E9FB8; margin-top:2px;">
                    Here's what's happening in the GTA VI universe.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with head_right:
        st.markdown("""
            <div style="display:flex; align-items:center; justify-content:flex-end; gap:14px; margin-top:4px;">
                <div style="background:#0B1120; border:1px solid #1E293B; border-radius:20px; padding:6px 14px; display:flex; align-items:center; gap:8px; width:220px;">
                    <span style="color:#64748B; font-size:0.8rem;">🔍</span>
                    <input type="text" placeholder="Search news, videos..." style="background:transparent; border:none; outline:none; color:#FFF; font-size:0.78rem; width:100%; font-family:inherit;" />
                </div>
                <div style="position:relative; cursor:pointer;">
                    <span style="font-size:1.15rem; color:#8E9FB8;">🔔</span>
                    <span style="position:absolute; top:-2px; right:-2px; width:7px; height:7px; background:#EF4444; border-radius:50%;"></span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:34px; height:34px; border-radius:50%; background:#FF2E93; display:flex; align-items:center; justify-content:center; font-size:1rem; box-shadow:0 0 12px rgba(255,46,147,0.4);">
                        🌴
                    </div>
                    <div>
                        <div style="font-size:0.82rem; font-weight:700; color:#FFF; line-height:1.1;">VicePlug</div>
                        <div style="font-size:0.68rem; color:#8E9FB8;">Creator Mode</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. Row 1: 5 Metric Cards with Glowing Sparklines
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown("""
            <div class="metric-card-box">
                <div class="metric-header">
                    <div class="metric-icon-circle" style="background:linear-gradient(135deg, #FF3B69, #FF5E80);">🔥</div>
                    <div class="metric-label-text">Trending Stories</div>
                </div>
                <div class="metric-val-row">
                    <div class="metric-number-big">47</div>
                    <svg width="75" height="26" viewBox="0 0 100 30" fill="none">
                        <path d="M 0 25 Q 20 15, 35 20 T 65 18 T 85 8 T 100 5" stroke="#A855F7" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div style="font-size:0.75rem; color:#10B981; font-weight:600; margin-top:4px;">↑ +32%</div>
            </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown("""
            <div class="metric-card-box">
                <div class="metric-header">
                    <div class="metric-icon-circle" style="background:linear-gradient(135deg, #2563EB, #00D2FF);">▶</div>
                    <div class="metric-label-text">Videos Discovered</div>
                </div>
                <div class="metric-val-row">
                    <div class="metric-number-big">138</div>
                    <svg width="75" height="26" viewBox="0 0 100 30" fill="none">
                        <path d="M 0 22 Q 25 18, 45 25 T 75 14 T 100 8" stroke="#00D2FF" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div style="font-size:0.75rem; color:#10B981; font-weight:600; margin-top:4px;">↑ +68%</div>
            </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown("""
            <div class="metric-card-box">
                <div class="metric-header">
                    <div class="metric-icon-circle" style="background:linear-gradient(135deg, #F59E0B, #FBBF24);">⭐</div>
                    <div class="metric-label-text">Avg Viral Score</div>
                </div>
                <div class="metric-val-row">
                    <div class="metric-number-big">92<span style="font-size:1.1rem; color:#8E9FB8; font-weight:500;">/100</span></div>
                    <svg width="75" height="26" viewBox="0 0 100 30" fill="none">
                        <path d="M 0 25 Q 30 20, 50 15 T 80 18 T 100 6" stroke="#10B981" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div style="font-size:0.75rem; color:#10B981; font-weight:600; margin-top:4px;">↑ +12%</div>
            </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown("""
            <div class="metric-card-box">
                <div class="metric-header">
                    <div class="metric-icon-circle" style="background:linear-gradient(135deg, #F43F5E, #FB7185);">📄</div>
                    <div class="metric-label-text">Pending Reviews</div>
                </div>
                <div class="metric-val-row">
                    <div class="metric-number-big">12</div>
                    <svg width="75" height="26" viewBox="0 0 100 30" fill="none">
                        <path d="M 0 10 Q 25 22, 50 16 T 75 24 T 100 20" stroke="#F43F5E" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div style="font-size:0.75rem; color:#F43F5E; font-weight:600; margin-top:4px;">↓ -8%</div>
            </div>
        """, unsafe_allow_html=True)

    with k5:
        st.markdown("""
            <div class="metric-card-box">
                <div class="metric-header">
                    <div class="metric-icon-circle" style="background:linear-gradient(135deg, #10B981, #34D399);">✓</div>
                    <div class="metric-label-text">Approved Content</div>
                </div>
                <div class="metric-val-row">
                    <div class="metric-number-big">34</div>
                    <svg width="75" height="26" viewBox="0 0 100 30" fill="none">
                        <path d="M 0 24 Q 25 26, 50 18 T 75 12 T 100 7" stroke="#10B981" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div style="font-size:0.75rem; color:#10B981; font-weight:600; margin-top:4px;">↑ +41%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3. Row 2: 4 Middle Panels
    c_stories, c_opp, c_video, c_pipe = st.columns([1.5, 1.25, 1.15, 0.95], gap="small")

    # Panel 1: Trending GTA VI Stories
    with c_stories:
        st.markdown("""
            <div class="panel-box">
                <div class="panel-header-title">
                    <span>Trending GTA VI Stories</span>
                    <span style="font-size:0.75rem; color:#8E9FB8; font-weight:500; cursor:pointer;">View All ➔</span>
                </div>
        """, unsafe_allow_html=True)

        stories_data = [
            ("1", b64_st1, "GTA VI Hidden Details Found in New Trailer", "Community spots possible new location...", "95"),
            ("2", b64_st2, "Vice City Expansion Theory Gains Traction", "New evidence suggests a larger map...", "91"),
            ("3", b64_st3, "Rockstar Hiring Spree Continues", "Multiple job listings hint at major features...", "89"),
            ("4", b64_st4, "Possible Release Window Leak", "Retail listing sparks new speculation...", "87"),
        ]

        for s_idx, s_b64, s_title, s_sub, s_score in stories_data:
            img_tag = f'<img src="data:image/jpeg;base64,{s_b64}" class="story-thumb-img" />' if s_b64 else '<div class="story-thumb-img"></div>'
            st.markdown(f"""
                <div class="story-row-item">
                    <span class="story-index-num">{s_idx}</span>
                    {img_tag}
                    <div style="flex-grow:1; min-width:0;">
                        <div style="font-size:0.83rem; font-weight:600; color:#FFF; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{s_title}</div>
                        <div style="font-size:0.72rem; color:#8E9FB8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{s_sub}</div>
                    </div>
                    <div class="story-score-pill">
                        {s_score} <span style="font-size:0.7rem;">🔥</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Panel 2: AI Opportunity Engine
    with c_opp:
        st.markdown("""
            <div class="panel-box">
                <div class="panel-header-title">
                    <span>🧠 AI Opportunity Engine</span>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
                    <!-- Circular SVG Donut Gauge -->
                    <div style="position:relative; width:88px; height:88px;">
                        <svg width="88" height="88" viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="40" stroke="#131B2E" stroke-width="8" fill="none" />
                            <defs>
                                <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stop-color="#FF2E93" />
                                    <stop offset="100%" stop-color="#A855F7" />
                                </linearGradient>
                            </defs>
                            <circle cx="50" cy="50" r="40" stroke="url(#gaugeGrad)" stroke-width="8" stroke-dasharray="238, 251" stroke-linecap="round" fill="none" transform="rotate(-90 50 50)" />
                        </svg>
                        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                            <div style="font-family:'Space Grotesk'; font-size:1.35rem; font-weight:800; color:#FFF; line-height:1;">95</div>
                            <div style="font-size:0.65rem; color:#8E9FB8;">/100</div>
                        </div>
                    </div>
                    <!-- Badges -->
                    <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-end;">
                        <span style="font-size:0.72rem; color:#CBD5E1; background:#182238; padding:3px 10px; border-radius:12px; font-weight:600;">High Potential</span>
                        <span style="font-size:0.72rem; color:#10B981; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); padding:3px 10px; border-radius:12px; font-weight:700;">Trending Now</span>
                    </div>
                </div>

                <!-- Recommended Content Callout -->
                <div style="background:#090E1B; border:1px solid #1C263D; border-radius:10px; padding:10px 12px; margin-bottom:12px;">
                    <div style="font-size:0.72rem; font-weight:600; color:#38BDF8; margin-bottom:4px;">Recommended Content</div>
                    <div style="display:flex; gap:6px; font-size:0.78rem; color:#CBD5E1; line-height:1.4;">
                        <span>💡</span>
                        <span>"Create a comparison video between GTA V and GTA VI map locations within next 8 hours."</span>
                    </div>
                </div>

                <!-- Potential & Confidence -->
                <div style="display:flex; justify-content:space-between; font-size:0.74rem;">
                    <div>
                        <div style="color:#8E9FB8; font-size:0.68rem;">Potential Reach</div>
                        <div style="color:#10B981; font-weight:700; font-size:0.9rem;">High</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#8E9FB8; font-size:0.68rem;">AI Confidence</div>
                        <div style="color:#A855F7; font-weight:700; font-size:0.9rem;">94%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Panel 3: Video Discovery
    with c_video:
        video_thumb_tag = f'<img src="data:image/jpeg;base64,{b64_vt}" style="width:100%; border-radius:8px; display:block;" />' if b64_vt else '<div style="height:90px; background:#1E293B; border-radius:8px;"></div>'
        st.markdown(f"""
            <div class="panel-box">
                <div class="panel-header-title">
                    <span>🎬 Video Discovery</span>
                    <span style="font-size:0.75rem; color:#8E9FB8; font-weight:500; cursor:pointer;">View All ➔</span>
                </div>
                <div style="font-size:0.74rem; font-weight:600; color:#FFF; margin-bottom:8px;">Top Performing Video</div>
                <div style="position:relative; margin-bottom:8px;">
                    {video_thumb_tag}
                </div>
                <div style="font-size:0.8rem; font-weight:600; color:#FFF; margin-bottom:8px; line-height:1.3;">
                    GTA VI Hidden Details That Change Everything
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; border-top:1px solid rgba(255,255,255,0.06); padding-top:6px;">
                    <div>
                        <b style="color:#FFF;">1.2M</b> <span style="color:#8E9FB8; font-size:0.68rem;">Views</span>
                    </div>
                    <div style="color:#10B981; font-weight:700;">
                        ↑ +245% <span style="font-size:0.68rem; color:#8E9FB8; font-weight:400;">Growth</span>
                    </div>
                    <div style="text-align:right;">
                        <b style="color:#FFF;">94%</b> <span style="color:#8E9FB8; font-size:0.68rem;">AI Conf.</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Panel 4: Content Pipeline
    with c_pipe:
        st.markdown("""
            <div class="panel-box">
                <div class="panel-header-title">
                    <span>Content Pipeline</span>
                </div>
                <div style="display:flex; flex-direction:column; gap:8px; font-size:0.8rem; margin-top:6px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; background:#10B981; color:#000; display:flex; align-items:center; justify-content:center; font-size:0.65rem; font-weight:800;">✓</span>
                        <span style="color:#FFF; font-weight:600;">Research</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; background:#10B981; color:#000; display:flex; align-items:center; justify-content:center; font-size:0.65rem; font-weight:800;">✓</span>
                        <span style="color:#FFF; font-weight:600;">AI Analysis</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; background:#10B981; color:#000; display:flex; align-items:center; justify-content:center; font-size:0.65rem; font-weight:800;">✓</span>
                        <span style="color:#FFF; font-weight:600;">Hook Created</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; background:#10B981; color:#000; display:flex; align-items:center; justify-content:center; font-size:0.65rem; font-weight:800;">✓</span>
                        <span style="color:#FFF; font-weight:600;">Script Draft</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; border:2px solid #00F5FF; display:inline-block;"></span>
                        <span style="color:#FFF; font-weight:600;">In Review</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; border:2px solid #64748B; display:inline-block;"></span>
                        <span style="color:#8E9FB8;">Approved</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:18px; height:18px; border-radius:50%; border:2px solid #64748B; display:inline-block;"></span>
                        <span style="color:#8E9FB8;">Published</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==================================================
# BOTTOM LIVE TICKER (MATCHING MOCKUP EXACTLY)
# ==================================================
st.markdown("""
    <div class="bottom-ticker-bar">
        <div style="display:flex; align-items:center; gap:12px; overflow:hidden; white-space:nowrap;">
            <span class="live-pill">● LIVE</span>
            <span style="font-weight:700; color:#FFF; font-size:0.8rem; letter-spacing:0.04em;">GTA VI NEWS FEED</span>
            <span style="color:#64748B;">|</span>
            <span style="color:#CBD5E1; font-size:0.78rem;">
                Rockstar releases new artwork &nbsp;•&nbsp; 
                Community finds new Vice City location &nbsp;•&nbsp; 
                Take-Two confirms development on track &nbsp;•&nbsp; 
                New gameplay details surface online &nbsp;•&nbsp; 
                GTA VI trending on YouTube (+320%)
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:10px; font-size:0.75rem; color:#8E9FB8; white-space:nowrap; margin-left:16px;">
            <span>STAY AHEAD. STAY PLUGGED.</span>
            <span style="font-family:'Space Grotesk'; font-weight:800; color:#FFF; font-size:0.95rem;">VI</span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # Close command-center-frame


# ==================================================
# INTERACTIVE WORKSPACE DRAWER (IF OTHER TABS CLICKED)
# ==================================================
if st.session_state["active_tab"] != "Dashboard":
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:#090E1B; border:1px solid #A855F7; border-radius:14px; padding:20px; box-shadow:0 0 25px rgba(168,85,247,0.25);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="font-family:'Space Grotesk'; font-size:1.3rem; font-weight:700; color:#FFF;">
                    Active Workspace: <span style="color:#FF2E93;">{st.session_state['active_tab']}</span>
                </div>
            </div>
    """, unsafe_allow_html=True)

    if st.session_state["active_tab"] in ["AI Studio", "Script Generator"]:
        st.markdown("<p style='font-size:0.85rem; color:#8E9FB8;'>Generate ready-to-cut 30-second Short scripts, high-CTR spoken hooks, and mobile on-screen text using Groq Llama-3.3:</p>", unsafe_allow_html=True)
        sample_title = st.text_input("GTA VI Video Opportunity Topic", value="GTA VI Hidden Details Found in New Trailer That Change Everything")
        if st.button("✨ Run Groq Script Synthesis", type="primary"):
            with st.spinner("Generating viral hook and 30s voiceover script..."):
                groq_key = get_secret("GROQ_API_KEY")
                if groq_key and HAS_GROQ:
                    try:
                        client = Groq(api_key=groq_key)
                        res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are VicePlug Hub's viral GTA VI scriptwriter. Return JSON with 'hook', 'script', 'on_screen_text', 'why_it_works'."},
                                {"role": "user", "content": f"Topic: {sample_title}"}
                            ],
                            response_format={"type": "json_object"}
                        )
                        parsed = json.loads(res.choices[0].message.content or "{}")
                        st.json(parsed)
                    except Exception as e:
                        st.error(f"Groq API error: {e}")
                else:
                    st.success("Demo Mode (Add GROQ_API_KEY in Secrets for live generation):")
                    st.markdown("""
                        **🎣 Spoken Hook (0–3s):** *"Rockstar hid a detail in plain sight in shot 14, and nobody noticed until today..."*  
                        **📝 30s Voiceover Script:** *"Look closely at the water reflection in the marina scene. That is not pre-baked lighting. Rockstar patented a real-time raytraced wake simulation engine that reacts to engine RPM. Here is why that matters for the map scale..."*  
                        **📱 On-Screen Overlay:** `TRAILER SECRET FOUND`
                    """)

    elif st.session_state["active_tab"] == "Google Sheets Sync":
        st.markdown("<p style='font-size:0.85rem; color:#8E9FB8;'>Bi-directional spreadsheet sync with your connected Google Sheet document.</p>", unsafe_allow_html=True)
        demo_table = pd.DataFrame([
            {"Title": "GTA VI Hidden Details Found in New Trailer", "Priority": 95, "Fact Status": "Official", "Status": "In Review"},
            {"Title": "Vice City Expansion Theory Gains Traction", "Priority": 91, "Fact Status": "Speculation", "Status": "Script Draft"},
            {"Title": "Rockstar Hiring Spree Continues", "Priority": 89, "Fact Status": "Press", "Status": "Approved"},
            {"Title": "Possible Release Window Leak", "Priority": 87, "Fact Status": "Leak", "Status": "Published"}
        ])
        st.dataframe(demo_table, use_container_width=True, hide_index=True)

    else:
        st.info(f"Workspace for '{st.session_state['active_tab']}' is ready. Click 'Dashboard' in the sidebar to return to the mockup command center.")

    st.markdown("</div>", unsafe_allow_html=True)
