"""VicePlug Hub — GTA VI research and content operations dashboard.

Designed for Streamlit Community Cloud. Connects to Google Sheets and Groq
when credentials are supplied in Streamlit Secrets.
"""

import json
import os
import html
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd
import streamlit as st

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

# -----------------------------------------------------------------------------
# Page configuration and visual system
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VicePlug Hub | GTA VI Intelligence",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {
  --vp-bg:#070914;
  --vp-bg-raised:#0b1020;
  --vp-surface:#0f1729;
  --vp-surface-2:#111d32;
  --vp-border:rgba(160,177,211,.14);
  --vp-border-strong:rgba(174,115,255,.32);
  --vp-pink:#ff4fa0;
  --vp-pink-strong:#ff2c8c;
  --vp-purple:#a78bfa;
  --vp-cyan:#55dff2;
  --vp-green:#4adea6;
  --vp-amber:#f4c36a;
  --vp-text:#f5f7ff;
  --vp-muted:#a0aec7;
  --vp-dim:#6f7f9d;
  --vp-radius:18px;
}

html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--vp-text); }
.stApp {
  color:var(--vp-text);
  background:
    radial-gradient(ellipse at 88% 2%, rgba(119,50,173,.16), transparent 30%),
    radial-gradient(ellipse at 3% 38%, rgba(30,112,145,.08), transparent 30%),
    var(--vp-bg);
}
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:rgba(7,9,20,.7); }
.block-container { max-width:1760px; padding:1.05rem 1.45rem 2.5rem; }

/* App frame and navigation */
div[data-testid="column"] { min-width:0; }
div[data-testid="column"]:has([class*="st-key-nav_Dashboard"]) {
  align-self:stretch;
  background:linear-gradient(180deg,rgba(18,25,46,.96),rgba(9,14,27,.98));
  border:1px solid var(--vp-border);
  border-radius:22px;
  padding:18px 13px 20px;
  box-shadow:0 16px 48px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.025);
}
.vp-logo-lockup { display:flex; align-items:center; gap:11px; margin:2px 4px 20px; }
.vp-logo-mark {
  display:grid; place-items:center; flex:0 0 43px; height:43px; border-radius:14px;
  color:#fff; font:800 1rem 'Space Grotesk',sans-serif; letter-spacing:-.08em;
  background:linear-gradient(145deg,#ff4fa0,#8b5cf6 78%);
  box-shadow:0 8px 26px rgba(205,57,161,.24),inset 0 1px 0 rgba(255,255,255,.3);
}
.vp-brand { font-family:'Space Grotesk',sans-serif; font-size:1.03rem; line-height:1.1; font-weight:700; letter-spacing:-.045em; margin:0; color:#fff; }
.vp-brand span { color:var(--vp-pink); }
.vp-logo-sub { margin-top:4px; color:#8391ae; font-size:.61rem; letter-spacing:.15em; font-weight:700; }
.vp-nav-group { margin:18px 8px 7px; color:#697995; font-size:.62rem; letter-spacing:.16em; font-weight:800; text-transform:uppercase; }
.vp-nav-group:first-of-type { margin-top:4px; }
div[class*="st-key-nav_"] { margin:0 0 5px; }
div[class*="st-key-nav_"] button {
  min-height:42px; padding:8px 11px !important; border-radius:11px !important;
  border:1px solid transparent !important; background:transparent !important;
  color:#9eacc4 !important; font-size:.82rem !important; font-weight:600 !important;
  text-align:left !important; box-shadow:none !important; transition:all .18s ease;
}
div[class*="st-key-nav_"] button:hover {
  color:#fff !important; background:rgba(255,255,255,.045) !important;
  border-color:rgba(255,255,255,.05) !important; transform:translateX(2px);
}
div[class*="st-key-nav_"] button[kind="primary"] {
  color:#fff !important; border-color:rgba(255,79,160,.26) !important;
  background:linear-gradient(95deg,rgba(255,47,139,.2),rgba(139,92,246,.11)) !important;
  box-shadow:inset 3px 0 0 var(--vp-pink),0 7px 22px rgba(0,0,0,.12) !important;
}
.vp-nav-foot { margin:26px 8px 0; padding-top:14px; border-top:1px solid var(--vp-border); color:#6f7f9d; font-size:.66rem; line-height:1.65; }

/* Typography and page headings */
h1,h2,h3,h4 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em; }
.vp-eyebrow { font-size:.66rem; font-weight:800; letter-spacing:.18em; color:#c7a6ff; text-transform:uppercase; }
.vp-page-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; border-bottom:1px solid var(--vp-border); padding:0 0 1.15rem; margin:0 0 1.25rem; }
.vp-page-head h1 { font-size:clamp(1.65rem,2vw,2rem); line-height:1.12; margin:.32rem 0 .35rem; }
.vp-page-head p { color:var(--vp-muted); margin:.25rem 0 0; font-size:.9rem; line-height:1.55; max-width:780px; }
.vp-pill { display:inline-flex; align-items:center; gap:7px; border:1px solid rgba(167,139,250,.25); color:#dfd1ff; background:rgba(111,66,193,.12); border-radius:999px; padding:6px 10px; font-size:.65rem; font-weight:800; white-space:nowrap; letter-spacing:.04em; }
.vp-pill:before { content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--vp-purple); box-shadow:0 0 9px rgba(167,139,250,.65); }
.vp-muted { color:var(--vp-muted); font-size:.83rem; line-height:1.55; }

/* Dashboard hero */
.vp-hero {
  display:grid; grid-template-columns:minmax(0,1.35fr) minmax(230px,.75fr); align-items:center; gap:24px;
  min-height:270px; position:relative; overflow:hidden; isolation:isolate;
  border:1px solid rgba(183,123,255,.25); border-radius:25px; padding:30px 34px; margin:0 0 24px;
  background:radial-gradient(ellipse at 81% 18%,rgba(255,57,153,.2),transparent 29%),
    radial-gradient(ellipse at 67% 100%,rgba(68,201,237,.12),transparent 34%),
    linear-gradient(118deg,#11172b 0%,#171329 48%,#27142e 100%);
  box-shadow:0 22px 65px rgba(0,0,0,.19),inset 0 1px 0 rgba(255,255,255,.04);
}
.vp-hero:before { content:""; position:absolute; inset:0; z-index:-1; opacity:.17; background-image:linear-gradient(rgba(180,194,230,.13) 1px,transparent 1px),linear-gradient(90deg,rgba(180,194,230,.13) 1px,transparent 1px); background-size:35px 35px; mask-image:linear-gradient(90deg,black,transparent 90%); }
.vp-hero-copy { position:relative; z-index:2; }
.vp-hero-topline { display:flex; align-items:center; gap:9px; color:#c4b5fd; font-size:.65rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
.vp-live-dot { width:7px; height:7px; display:inline-block; background:var(--vp-green); border-radius:50%; box-shadow:0 0 13px rgba(74,222,166,.8); }
.vp-hero h1 { font-family:'Space Grotesk',sans-serif; font-size:clamp(2rem,3.1vw,3.15rem); line-height:1.02; letter-spacing:-.065em; margin:.8rem 0 .8rem; color:#fff; }
.vp-hero h1 span { background:linear-gradient(90deg,#ff77b9,#d3a5ff 58%,#76e7ff); color:transparent; -webkit-background-clip:text; background-clip:text; }
.vp-hero p { color:#b0bad0; max-width:660px; font-size:.91rem; line-height:1.65; margin:0; }
.vp-hero-tags { display:flex; gap:8px; flex-wrap:wrap; margin-top:20px; }
.vp-hero-tags span { padding:6px 9px; border:1px solid rgba(203,213,225,.13); background:rgba(6,9,19,.24); color:#d7deed; border-radius:8px; font-size:.65rem; font-weight:700; letter-spacing:.035em; }
.vp-hero-art { min-height:194px; position:relative; display:grid; place-items:center; overflow:hidden; border:1px solid rgba(255,255,255,.1); border-radius:20px; background:linear-gradient(145deg,rgba(9,14,29,.26),rgba(7,9,20,.64)); }
.vp-hero-art:before { content:""; position:absolute; inset:0; background:radial-gradient(circle at 51% 48%,rgba(255,79,160,.2),transparent 42%),linear-gradient(transparent 96%,rgba(85,223,242,.15) 100%); }
.vp-orbit { position:absolute; left:50%; top:50%; border:1px solid rgba(167,139,250,.35); border-radius:50%; transform:translate(-50%,-50%) rotate(-18deg); }
.vp-orbit-one { width:185px; height:185px; }
.vp-orbit-two { width:135px; height:200px; border-color:rgba(255,79,160,.36); transform:translate(-50%,-50%) rotate(48deg); }
.vp-orbit-three { width:225px; height:83px; border-color:rgba(85,223,242,.28); transform:translate(-50%,-50%) rotate(-34deg); }
.vp-hero-core { z-index:1; width:88px; height:88px; border-radius:27px; display:grid; place-items:center; font:700 1.85rem 'Space Grotesk',sans-serif; letter-spacing:-.09em; color:white; background:linear-gradient(145deg,rgba(255,79,160,.93),rgba(113,76,225,.93)); border:1px solid rgba(255,255,255,.4); box-shadow:0 0 38px rgba(216,65,179,.36),inset 0 1px 0 rgba(255,255,255,.35); transform:rotate(-8deg); }
.vp-hero-code { position:absolute; color:#a8bad8; font:700 .58rem 'Space Grotesk',sans-serif; letter-spacing:.13em; }
.vp-hero-code.top { top:13px; left:14px; }
.vp-hero-code.bottom { bottom:13px; right:14px; color:#f4a9d4; }

/* Metric and content cards */
.vp-card { height:100%; min-height:132px; background:linear-gradient(155deg,rgba(20,29,49,.96),rgba(12,18,33,.96)); border:1px solid var(--vp-border); border-radius:17px; padding:17px 17px 15px; box-shadow:0 10px 26px rgba(0,0,0,.11),inset 0 1px 0 rgba(255,255,255,.025); transition:transform .18s ease,border-color .18s ease; }
.vp-card:hover { transform:translateY(-2px); border-color:rgba(167,139,250,.27); }
.vp-metric-label { color:#a6b3ca; font-size:.75rem; font-weight:650; }
.vp-metric-value { font-family:'Space Grotesk',sans-serif; font-size:clamp(1.65rem,2vw,2rem); font-weight:700; line-height:1.15; letter-spacing:-.045em; margin:.52rem 0 .25rem; color:#fff; }
.vp-metric-note { color:#71819f; font-size:.69rem; line-height:1.45; }
.vp-panel { background:linear-gradient(155deg,rgba(15,23,41,.91),rgba(10,16,30,.96)); border:1px solid var(--vp-border); border-radius:17px; padding:18px; margin-bottom:13px; box-shadow:0 10px 28px rgba(0,0,0,.09),inset 0 1px 0 rgba(255,255,255,.02); }
.vp-panel-title { font-family:'Space Grotesk',sans-serif; font-size:1.02rem; font-weight:700; letter-spacing:-.025em; margin:0 0 .4rem; color:#f4f6ff; }
.vp-empty { text-align:center; padding:38px 20px; border:1px dashed rgba(138,158,194,.28); border-radius:17px; color:var(--vp-muted); background:rgba(14,23,41,.32); line-height:1.6; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid var(--vp-border); border-radius:13px; overflow:hidden; }

/* Inputs, buttons, tables and controls */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
  background:#0c1425 !important; border-color:#293750 !important; border-radius:11px !important; color:#f4f7ff !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus { border-color:rgba(167,139,250,.8) !important; box-shadow:0 0 0 1px rgba(167,139,250,.25) !important; }
.stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a {
  min-height:2.55rem; border-radius:11px; border:1px solid #293750; background:#111a2d; color:#eaf0fc;
  font-weight:650; transition:all .18s ease; box-shadow:none;
}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stLinkButton"] a:hover { border-color:rgba(167,139,250,.55); color:#fff; background:#17172c; transform:translateY(-1px); }
button[kind="primary"] { background:linear-gradient(105deg,#df3b95,#8458e9) !important; border:1px solid rgba(255,255,255,.09) !important; color:#fff !important; box-shadow:0 8px 24px rgba(184,63,169,.17) !important; }
button[kind="primary"]:hover { filter:brightness(1.09); box-shadow:0 10px 27px rgba(184,63,169,.24) !important; }
.stRadio [role="radiogroup"], .stCheckbox, .stSlider { color:var(--vp-text); }
[data-testid="stAlert"] { border-radius:13px; border-width:1px; }
[data-testid="stExpander"] { border:1px solid var(--vp-border); border-radius:13px; overflow:hidden; background:rgba(11,17,32,.6); }
[data-testid="stTabs"] button { font-weight:650; }
[data-testid="stCaptionContainer"] { color:#8292ad; }
label, [data-testid="stWidgetLabel"] { color:#cbd5e1 !important; font-weight:600 !important; }

/* ------------------------------------------------------------------
   Refined, spacious content system — less compact, more editorial
   ------------------------------------------------------------------ */
.block-container { max-width: 1840px; padding: 1.35rem 1.8rem 3.2rem; }
.vp-page-head { padding-bottom: 1.55rem; margin-bottom: 1.8rem; gap: 1.5rem; }
.vp-page-head h1 { font-size: clamp(1.9rem, 2.3vw, 2.45rem); margin: .45rem 0 .55rem; }
.vp-page-head p { font-size: .98rem; line-height: 1.75; max-width: 900px; }
.vp-eyebrow { font-size: .7rem; letter-spacing: .2em; }
.vp-hero { min-height: 310px; padding: 38px 42px; margin-bottom: 30px; gap: 32px; }
.vp-hero h1 { font-size: clamp(2.35rem, 3.4vw, 3.5rem); }
.vp-hero p { font-size: 1rem; line-height: 1.8; }
.vp-hero-art { min-height: 222px; }
.vp-card { min-height: 150px; padding: 22px 22px 20px; border-radius: 20px; }
.vp-metric-label { font-size: .82rem; }
.vp-metric-value { font-size: clamp(1.9rem, 2.2vw, 2.35rem); margin: .7rem 0 .35rem; }
.vp-metric-note { font-size: .76rem; line-height: 1.6; }
.vp-panel { padding: 23px; margin-bottom: 18px; border-radius: 20px; }
.vp-panel-title { font-size: 1.12rem; margin-bottom: .6rem; }
.vp-muted { font-size: .9rem; line-height: 1.75; }
.vp-empty { padding: 54px 26px; font-size: .95rem; }
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
  min-height: 46px !important; border-radius: 13px !important; font-size: .94rem !important;
}
.stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a {
  min-height: 2.9rem; border-radius: 13px; padding-left: 16px; padding-right: 16px;
}
.stSlider { padding-top: .55rem; padding-bottom: .45rem; }
.stSlider [data-baseweb="slider"] { padding-top: .4rem; padding-bottom: .5rem; }
.stSlider [role="slider"] { border: 3px solid #fff !important; box-shadow: 0 0 0 5px rgba(255,79,160,.16), 0 0 22px rgba(255,79,160,.45) !important; }
.stSlider [data-testid="stTickBar"] { display: none; }
.stRadio [role="radiogroup"] { gap: 10px; }
.stRadio [role="radio"] { padding: 8px 13px; border-radius: 12px; }
.vp-record-card {
  display:flex; flex-direction:column; gap:13px; min-height:260px; height:100%;
  padding:23px 23px 20px; margin:0 0 6px; border-radius:20px;
  background:linear-gradient(150deg,rgba(20,30,52,.98),rgba(10,16,30,.98));
  border:1px solid rgba(153,173,211,.16);
  box-shadow:0 16px 36px rgba(0,0,0,.15),inset 0 1px 0 rgba(255,255,255,.035);
  transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease;
  overflow-wrap:anywhere;
}
.vp-record-card:hover { transform:translateY(-3px); border-color:rgba(183,123,255,.43); box-shadow:0 20px 44px rgba(0,0,0,.21),0 0 24px rgba(145,78,220,.07); }
.vp-record-top { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.vp-record-kicker { color:#8494b0; font-size:.66rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }
.vp-record-score { display:inline-flex; align-items:center; gap:6px; border:1px solid rgba(255,79,160,.32); color:#ff9fce; background:rgba(255,79,160,.09); padding:6px 10px; border-radius:999px; font:700 .76rem 'Space Grotesk',sans-serif; white-space:nowrap; }
.vp-record-card h3 { font:700 1.12rem/1.45 'Space Grotesk',sans-serif; letter-spacing:-.025em; color:#f7f8ff; margin:0; }
.vp-record-summary { color:#a8b5cc; font-size:.88rem; line-height:1.75; margin:0; }
.vp-record-chips { display:flex; flex-wrap:wrap; align-items:center; gap:7px; margin-top:1px; }
.vp-record-chip { display:inline-flex; align-items:center; gap:5px; color:#c9d4e8; font-size:.69rem; font-weight:650; padding:6px 9px; border-radius:9px; border:1px solid rgba(151,169,202,.14); background:rgba(7,11,23,.46); }
.vp-record-chip.status { color:#d9c8ff; border-color:rgba(167,139,250,.22); background:rgba(130,83,223,.1); }
.vp-record-chip.fact { color:#ffdca2; border-color:rgba(244,195,106,.22); background:rgba(244,195,106,.07); }
.vp-record-meta { display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px; padding-top:2px; color:#72829e; font-size:.72rem; }
.vp-record-footer { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-top:auto; padding-top:13px; border-top:1px solid rgba(151,169,202,.12); }
.vp-record-footer a { color:#83e8f7; text-decoration:none; font-size:.78rem; font-weight:750; }
.vp-record-footer a:hover { color:#fff; text-decoration:underline; }
.vp-record-footer span { color:#72829e; font-size:.7rem; }
.vp-record-select { margin-top:-2px; padding:0 0 10px; }
.vp-brief-hero { border:1px solid rgba(255,79,160,.28); border-radius:22px; padding:25px; margin:10px 0 18px; background:radial-gradient(ellipse at 90% 5%,rgba(255,79,160,.14),transparent 35%),linear-gradient(140deg,#121a2e,#171327); }
.vp-brief-title { color:#fff; font:700 1.45rem/1.35 'Space Grotesk',sans-serif; letter-spacing:-.035em; margin:0 0 10px; }
.vp-brief-lead { color:#e1d7ff; font-size:1.02rem; line-height:1.75; margin:0; }
.vp-brief-card { height:100%; min-height:135px; padding:21px; margin-bottom:15px; border-radius:17px; border:1px solid var(--vp-border); background:linear-gradient(150deg,rgba(17,27,47,.96),rgba(10,16,30,.96)); }
.vp-brief-card h4 { color:#d5b9ff; font-size:.75rem; line-height:1.4; letter-spacing:.13em; text-transform:uppercase; margin:0 0 12px; }
.vp-brief-card p { white-space:pre-wrap; color:#e1e7f3; font-size:.9rem; line-height:1.85; margin:0; }
.vp-brief-list { display:flex; flex-wrap:wrap; gap:7px; }
.vp-brief-tag { border:1px solid rgba(85,223,242,.2); background:rgba(85,223,242,.07); color:#adf2fb; border-radius:9px; padding:7px 10px; font-size:.78rem; }
.vp-card-grid-note { color:#7f90ad; font-size:.77rem; margin:0 0 13px; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border-radius:16px; }
@media (max-width: 1150px) {
  .block-container { padding:1rem 1rem 2.2rem; }
  .vp-hero { padding:28px; }
  .vp-record-card { min-height:240px; padding:19px; }
}
@media (max-width: 650px) {
  .block-container { padding:.7rem .55rem 1.6rem; }
  .vp-hero { min-height:0; padding:22px 18px; gap:18px; }
  .vp-hero h1 { font-size:2.2rem; }
  .vp-card { min-height:125px; padding:16px; }
  .vp-panel { padding:17px; }
  .vp-record-card { min-height:0; padding:18px; }
  .vp-brief-hero { padding:19px; }
  .vp-brief-card { padding:17px; }
}

/* Footer and subtle transitions */
.vp-footer { margin-top:26px; padding:15px 17px; border:1px solid var(--vp-border); border-radius:14px; background:rgba(9,14,27,.8); display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; color:#8190ab; font-size:.72rem; }
.vp-footer strong { color:var(--vp-pink); letter-spacing:.04em; }
@media (max-width: 1050px) {
  .block-container { padding:1rem .8rem 2rem; }
  .vp-hero { grid-template-columns:1fr; padding:25px; }
  .vp-hero-art { min-height:150px; }
  .vp-hero-art .vp-orbit-one { width:150px; height:150px; }
  .vp-hero-art .vp-orbit-two { height:165px; }
  .vp-page-head { align-items:flex-start; }
  .vp-page-head .vp-pill { display:none; }
}
@media (max-width: 650px) {
  .block-container { padding:.65rem .55rem 1.5rem; }
  .vp-hero { border-radius:18px; padding:21px 18px; gap:18px; }
  .vp-hero h1 { font-size:2rem; }
  .vp-hero p { font-size:.85rem; }
  .vp-hero-art { min-height:125px; }
  .vp-panel { padding:14px; border-radius:14px; }
  .vp-card { min-height:118px; padding:13px; }
  .vp-page-head { flex-direction:column; }
  div[data-testid="column"]:has([class*="st-key-nav_Dashboard"]) { padding:13px 9px; border-radius:16px; }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Configuration / integrations
# -----------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Research Feed", "📰"),
    ("Viral Opportunities", "🎯"),
    ("Video Discovery", "🎥"),
    ("AI Studio", "🧠"),
    ("Script Generator", "📝"),
    ("Content Pipeline", "⚡"),
    ("Review Queue", "☑️"),
    ("Trends & Analytics", "📈"),
    ("Google Sheets Sync", "📊"),
    ("Settings", "⚙️"),
]

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if "generated_script" not in st.session_state:
    st.session_state.generated_script = None


def get_secret(name: str, default: Any = None) -> Any:
    """Read a value from Streamlit Secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, default)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def get_service_account_info() -> Optional[Dict[str, Any]]:
    """Support the usual Streamlit [gcp_service_account] block or JSON secret."""
    try:
        info = st.secrets.get("gcp_service_account")
        if info and hasattr(info, "items"):
            return dict(info)
    except Exception:
        pass
    raw = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        try:
            return json.loads(raw) if isinstance(raw, str) else dict(raw)
        except Exception:
            return None
    return None


def ensure_worksheet_capacity(ws: Any, *, min_rows: Optional[int] = None, min_cols: Optional[int] = None) -> None:
    """Expand a Google worksheet before writing beyond its current grid."""
    current_rows = int(getattr(ws, "row_count", 1000) or 1000)
    current_cols = int(getattr(ws, "col_count", 26) or 26)
    target_rows = max(current_rows, int(min_rows or current_rows))
    target_cols = max(current_cols, int(min_cols or current_cols))
    if target_rows != current_rows or target_cols != current_cols:
        # gspread's resize accepts both dimensions, preserving the existing grid
        # while expanding only where needed.
        ws.resize(rows=target_rows, cols=target_cols)


def open_spreadsheet():
    if not HAS_GSPREAD:
        raise RuntimeError("Google Sheets packages are missing. Add gspread and google-auth to requirements.txt.")
    account_info = get_service_account_info()
    local_key_file = get_secret("GOOGLE_SERVICE_ACCOUNT_FILE")
    if account_info:
        credentials = Credentials.from_service_account_info(account_info, scopes=SCOPES)
        client = gspread.authorize(credentials)
    elif local_key_file and os.path.exists(str(local_key_file)):
        client = gspread.service_account(filename=str(local_key_file), scopes=SCOPES)
    else:
        raise RuntimeError("Google credentials are not configured in Streamlit Secrets.")

    sheet_id = get_secret("GOOGLE_SHEET_ID") or get_secret("SPREADSHEET_ID")
    sheet_name = get_secret("GOOGLE_SHEET_NAME") or get_secret("SPREADSHEET_NAME")
    if sheet_id:
        return client.open_by_key(str(sheet_id))
    if sheet_name:
        return client.open(str(sheet_name))
    raise RuntimeError("Set GOOGLE_SHEET_ID or GOOGLE_SHEET_NAME in Streamlit Secrets.")


def load_sheet_records() -> Tuple[pd.DataFrame, Any, str, str]:
    """Load a research worksheet. Returns dataframe, worksheet, message, status."""
    try:
        book = open_spreadsheet()
        preferred = str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))
        candidates = [preferred, "Research Feed", "AI Analysis", "Clip Queue", "Sheet1"]
        worksheet = None
        last_error = None
        for name in dict.fromkeys(candidates):
            try:
                worksheet = book.worksheet(name)
                break
            except Exception as exc:
                last_error = exc
        if worksheet is None:
            names = [ws.title for ws in book.worksheets()]
            if not names:
                return pd.DataFrame(), None, "The spreadsheet has no worksheets.", "empty"
            return pd.DataFrame(), None, "Could not find a research worksheet. Available tabs: " + ", ".join(names), "missing_tab"
        values = worksheet.get_all_values()
        if not values:
            return pd.DataFrame(), worksheet, f"Connected to {book.title} / {worksheet.title}, but the tab is empty.", "empty"
        headers = [str(h).strip() for h in values[0]]
        if not any(headers):
            return pd.DataFrame(), worksheet, f"The first row of {worksheet.title} must contain column headers.", "empty"
        # Prevent duplicate/blank column headings from breaking pandas operations.
        seen: Dict[str, int] = {}
        clean_headers = []
        for i, name in enumerate(headers):
            base = name or f"Column {i + 1}"
            seen[base] = seen.get(base, 0) + 1
            clean_headers.append(base if seen[base] == 1 else f"{base} ({seen[base]})")
        rows = values[1:]
        width = len(clean_headers)
        rows = [(row + [""] * max(0, width - len(row)))[:width] for row in rows]
        df = pd.DataFrame(rows, columns=clean_headers)
        df.insert(0, "_sheet_row", range(2, len(df) + 2))
        # Drop fully empty records but keep the original row number for safe updates.
        if len(df):
            visible_cols = [c for c in df.columns if c != "_sheet_row"]
            nonempty = df[visible_cols].astype(str).apply(lambda r: any(v.strip() for v in r), axis=1)
            df = df.loc[nonempty].reset_index(drop=True)
        return df, worksheet, f"Connected: {book.title} → {worksheet.title} · {len(df)} records", "connected"
    except Exception as exc:
        return pd.DataFrame(), None, str(exc), "error"


def first_matching_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    # Loose fallback only after exact variants fail.
    # Prefer the most specific phrase first (e.g. "Review Status" before "Status").
    for candidate in sorted(candidates, key=len, reverse=True):
        candidate = candidate.lower()
        for column in df.columns:
            normalized = str(column).strip().lower()
            if candidate in normalized:
                return column
    return None


def title_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["Title", "Video Title", "Topic", "Video", "Story Title", "Name"])


def url_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["Video URL", "Source URL", "YouTube URL", "URL", "Link", "Source Link"])


def score_column(df: pd.DataFrame) -> Optional[str]:
    """Return the most useful score column, preferring one with numeric values."""
    candidates = ["AI Priority Score", "Discovery Priority Score", "Priority Score", "Viral Score", "Priority", "Score"]
    found = []
    for candidate in candidates:
        col = first_matching_column(df, [candidate])
        if col and col not in found:
            found.append(col)
    for col in found:
        if df[col].apply(number_value).notna().any():
            return col
    return found[0] if found else None


def status_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["Review Status", "Pipeline Status", "Content Status", "Status"])


def fact_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["AI Fact Status", "Fact Status", "Verification Status"])


def number_value(value: Any) -> Optional[float]:
    try:
        text = str(value).strip().replace("%", "").replace(",", "")
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def sorted_by_score(df: pd.DataFrame) -> pd.DataFrame:
    col = score_column(df)
    if not col:
        return df.copy()
    output = df.copy()
    output["_numeric_score"] = output[col].apply(number_value)
    return output.sort_values("_numeric_score", ascending=False, na_position="last")


def clean_display_df(df: pd.DataFrame, max_cols: int = 9) -> pd.DataFrame:
    output = df.drop(columns=[c for c in ["_sheet_row"] if c in df.columns], errors="ignore").copy()
    return output.iloc[:, :max_cols]


def safe_text(value: Any, limit: int = 160) -> str:
    result = html.escape(str(value or "").strip())
    return result if len(result) <= limit else result[:limit - 1] + "…"



def _value_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text if text else default


def _row_first_value(row: Any, df: pd.DataFrame, candidates: List[str], default: str = "") -> str:
    col = first_matching_column(df, candidates)
    return _value_text(row.get(col, ""), default) if col else default


def render_record_cards(
    records: pd.DataFrame,
    *,
    key_prefix: str,
    max_items: int = 40,
    columns_count: int = 2,
    show_raw_expander: bool = False,
) -> None:
    '''Render Google Sheet records as spacious editorial cards, not a default grid.'''
    if records is None or records.empty:
        show_missing_data("No records match these filters.")
        return

    view = records.copy()
    if "_numeric_score" in view.columns:
        view = view.drop(columns=["_numeric_score"], errors="ignore")
    shown = view.head(max_items)
    st.markdown(
        f'<div class="vp-card-grid-note">Showing <b>{len(shown)}</b> of <b>{len(view)}</b> records · Open each original source before treating a claim as verified.</div>',
        unsafe_allow_html=True,
    )
    title_col = title_column(shown)
    source_col = first_matching_column(shown, ["Source", "Publisher", "Channel", "Source Domain", "Creator", "Website"])
    summary_col = first_matching_column(shown, [
        "AI Summary", "Summary", "AI Why It Matters", "Why It Matters", "Discovery Priority Reasons",
        "Description", "Moment Explanation", "Notes", "Research Type", "Commentary Draft"
    ])
    url_col = url_column(shown)
    score_col = score_column(shown)
    status_col_local = status_column(shown)
    fact_col_local = fact_column(shown)
    date_col = first_matching_column(shown, ["Published At", "Publication Date", "Date Published", "Indexed At", "Collected At (UTC)", "Date", "Timestamp"])

    items = list(shown.iterrows())
    count = max(1, min(3, columns_count))
    for offset in range(0, len(items), count):
        slots = st.columns(count, gap="large")
        for local_i, (record_index, row) in enumerate(items[offset:offset + count]):
            with slots[local_i]:
                title = safe_text(_value_text(row.get(title_col, ""), "Untitled research record"), 210) if title_col else "Untitled research record"
                summary_value = _value_text(row.get(summary_col, ""), "No summary saved yet. Open the original source to review the details.") if summary_col else "No summary saved yet. Open the original source to review the details."
                summary = safe_text(summary_value, 370)
                source = _value_text(row.get(source_col, ""), "") if source_col else ""
                url = _value_text(row.get(url_col, ""), "") if url_col else ""
                domain = ""
                if url.startswith(("https://", "http://")):
                    try:
                        domain = urlparse(url).netloc.lower().removeprefix("www.")
                    except Exception:
                        domain = ""
                source_label = safe_text(source or domain or "Source not recorded", 72)
                score_num = number_value(row.get(score_col)) if score_col else None
                score_chip = f'<span class="vp-record-score">{score_num:.0f}<span style="opacity:.7">/100</span></span>' if score_num is not None else '<span class="vp-record-kicker">UNSCORED</span>'
                status = safe_text(_value_text(row.get(status_col_local, ""), "Needs review") if status_col_local else "Needs review", 45)
                fact = safe_text(_value_text(row.get(fact_col_local, ""), "Unverified") if fact_col_local else "Unverified", 45)
                date_label = safe_text(_value_text(row.get(date_col, ""), "Date not recorded") if date_col else "Date not recorded", 48)
                row_number = _value_text(row.get("_sheet_row", ""), "")
                link_html = f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">Open original source ↗</a>' if url.startswith(("https://", "http://")) else '<span>No source URL saved</span>'
                st.markdown(
                    f'''<article class="vp-record-card">
                      <div class="vp-record-top"><span class="vp-record-kicker">RESEARCH RECORD</span>{score_chip}</div>
                      <h3>{title}</h3>
                      <p class="vp-record-summary">{summary}</p>
                      <div class="vp-record-chips"><span class="vp-record-chip">◈ {source_label}</span><span class="vp-record-chip status">{status}</span><span class="vp-record-chip fact">{fact}</span></div>
                      <div class="vp-record-meta"><span>◷ {date_label}</span><span>{f'Sheet row {html.escape(row_number)}' if row_number else html.escape(str(record_index + 1) if isinstance(record_index, int) else '')}</span></div>
                      <div class="vp-record-footer">{link_html}<span>Review before use</span></div>
                    </article>''',
                    unsafe_allow_html=True,
                )
    if len(view) > max_items:
        st.caption(f"{len(view) - max_items} more records are not shown in this card view. Use the search/filter controls to narrow the list.")
    if show_raw_expander:
        with st.expander("Advanced: inspect raw worksheet columns", expanded=False):
            st.dataframe(clean_display_df(records, 24), use_container_width=True, hide_index=True, height=340)


def _display_brief_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        chunks = [str(item).strip() for item in value if str(item).strip()]
        if not chunks:
            return "Not provided."
        return "\n".join(f"• {item}" for item in chunks)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return _value_text(value, "Not provided.")


def render_generated_brief(result: Dict[str, Any], mode: str = "AI brief") -> None:
    '''Render generated script/analysis data as editable-looking editorial sections.'''
    if not isinstance(result, dict):
        st.json(result)
        return
    title = _value_text(result.get("title"), "Your content draft")
    lead = _value_text(result.get("spoken_hook"), _value_text(result.get("hook"), _value_text(result.get("summary"), "Review the draft below and verify every factual claim.")))
    st.markdown(
        f'<section class="vp-brief-hero"><div class="vp-eyebrow">{html.escape(mode.upper())} · HUMAN REVIEW REQUIRED</div><div class="vp-brief-title">{safe_text(title, 220)}</div><p class="vp-brief-lead">{safe_text(lead, 650)}</p></section>',
        unsafe_allow_html=True,
    )
    field_groups = [
        ("Voiceover / commentary", ["voiceover_script", "commentary_draft", "script"]),
        ("Why this angle matters", ["why_this_angle", "why_it_matters", "recommended_action"]),
        ("On-screen text", ["on_screen_text"]),
        ("Caption", ["caption"]),
        ("Hashtags", ["hashtags"]),
        ("Verification checklist", ["verification_needed"]),
        ("Rights / usage note", ["rights_note"]),
        ("Timestamped beats", ["timestamped_beats"]),
    ]
    used = {"title", "spoken_hook", "hook", "summary"}
    cards = []
    for label, keys in field_groups:
        key = next((k for k in keys if k in result and result[k] not in (None, "", [], {})), None)
        if key:
            used.add(key)
            value = result[key]
            if isinstance(value, list) and label in ("Hashtags", "On-screen text"):
                tags = "".join(f'<span class="vp-brief-tag">{safe_text(x, 150)}</span>' for x in value if str(x).strip())
                content = f'<div class="vp-brief-list">{tags}</div>' if tags else '<p>Not provided.</p>'
            else:
                content = f'<p>{safe_text(_display_brief_value(value), 1500)}</p>'
            cards.append((label, content))
    for offset in range(0, len(cards), 2):
        cols = st.columns(2, gap="large")
        for col, (label, content) in zip(cols, cards[offset:offset + 2]):
            with col:
                st.markdown(f'<section class="vp-brief-card"><h4>{html.escape(label)}</h4>{content}</section>', unsafe_allow_html=True)
    other = [(k, v) for k, v in result.items() if k not in used and v not in (None, "", [], {})]
    if other:
        with st.expander("Additional AI fields", expanded=False):
            extra_cards = []
            for key, value in other:
                extra_cards.append((str(key).replace("_", " ").title(), safe_text(_display_brief_value(value), 1200)))
            for offset in range(0, len(extra_cards), 2):
                cols = st.columns(2, gap="large")
                for col, (label, content) in zip(cols, extra_cards[offset:offset + 2]):
                    with col:
                        st.markdown(f'<section class="vp-brief-card"><h4>{html.escape(label)}</h4><p>{content}</p></section>', unsafe_allow_html=True)


def call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 1600) -> Dict[str, Any]:
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in Streamlit Secrets.")
    if not HAS_GROQ:
        raise RuntimeError("The groq package is missing. Add groq to requirements.txt.")
    model = str(get_secret("GROQ_MODEL", "openai/gpt-oss-20b"))
    client = Groq(api_key=str(api_key))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=max_tokens,
        temperature=0.4,
    )
    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # A visible error is better than silently treating malformed output as valid.
        raise RuntimeError("Groq returned text that was not valid JSON. Try again or use a shorter source note.")


def render_page_header(title: str, subtitle: str, eyebrow: str = "VICEPLUG HUB") -> None:
    st.markdown(
        f'<div class="vp-page-head"><div><div class="vp-eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>'
        f'<span class="vp-pill">GTA VI · CREATOR WORKSPACE</span></div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str, emoji: str, accent: str) -> None:
    st.markdown(
        f'<div class="vp-card"><div style="display:flex;align-items:center;gap:9px">'
        f'<span style="width:30px;height:30px;display:grid;place-items:center;border-radius:50%;background:{accent}22">{emoji}</span>'
        f'<span class="vp-metric-label">{html.escape(label)}</span></div>'
        f'<div class="vp-metric-value">{html.escape(value)}</div>'
        f'<div class="vp-metric-note">{html.escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def show_missing_data(message: str = "Connect Google Sheets to show your real research records here.") -> None:
    st.markdown(f'<div class="vp-empty"><div style="font-size:1.5rem">🗂️</div><b>No research data loaded</b><br><span>{html.escape(message)}</span></div>', unsafe_allow_html=True)


def save_ai_brief_to_worksheet(worksheet_name: str, sheet_row: int, result: Dict[str, Any]) -> str:
    """Persist an AI brief into clearly named columns on the matching research row."""
    book = open_spreadsheet()
    ws = book.worksheet(worksheet_name)
    headers = [str(h).strip() for h in ws.row_values(1)]
    if not headers:
        raise RuntimeError(f"Worksheet '{worksheet_name}' has no header row.")

    fields = {
        "AI Relevance": "relevance",
        "AI Priority Score": "priority_score",
        "AI Fact Status": "fact_status",
        "AI Summary": "summary",
        "AI Why It Matters": "why_it_matters",
        "AI Hook": "hook",
        "AI Commentary Draft": "commentary_draft",
        "AI On-Screen Text": "on_screen_text",
        "AI Title": "title",
        "AI Caption": "caption",
        "AI Hashtags": "hashtags",
        "AI Verification Needed": "verification_needed",
        "AI Rights Note": "rights_note",
        "AI Recommended Action": "recommended_action",
        "AI Last Analyzed (UTC)": "_timestamp",
    }
    # Add the new AI columns only after expanding the worksheet grid. Existing
    # worksheets can have a fixed 11-column limit; writing column L without a
    # resize causes Google Sheets APIError 400.
    normalized_headers = [h.lower() for h in headers]
    missing_headings = [heading for heading in fields if heading.lower() not in normalized_headers]
    if missing_headings:
        ensure_worksheet_capacity(ws, min_cols=len(headers) + len(missing_headings))
        for heading in missing_headings:
            ws.update_cell(1, len(headers) + 1, heading)
            headers.append(heading)

    ensure_worksheet_capacity(ws, min_rows=int(sheet_row), min_cols=len(headers))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    for heading, key in fields.items():
        idx = next(i for i, h in enumerate(headers) if h.lower() == heading.lower())
        value = now if key == "_timestamp" else result.get(key, "")
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        ws.update_cell(int(sheet_row), idx + 1, str(value) if value is not None else "")

    # Mark as needing human review only when a status column exists and is blank.
    normalized = [h.lower() for h in headers]
    status_idx = next((i for i, h in enumerate(normalized) if h in ["review status", "pipeline status", "content status", "status"]), None)
    if status_idx is not None:
        existing_status = ws.cell(int(sheet_row), status_idx + 1).value
        if not str(existing_status or "").strip():
            ws.update_cell(int(sheet_row), status_idx + 1, "Needs Review")
    return f"Saved AI brief to {book.title} → {worksheet_name}, row {sheet_row}."


# -----------------------------------------------------------------------------
# Live news discovery (GDELT DOC API) and a dedicated Research Feed worksheet
# -----------------------------------------------------------------------------
NEWS_WORKSHEET_NAME = str(get_secret("NEWS_RESEARCH_WORKSHEET", "Research Feed"))
NEWS_DEFAULT_QUERY = '("Grand Theft Auto VI" OR "GTA VI" OR "GTA 6")'
NEWS_BASE_HEADERS = [
    "Title", "Source", "Source URL", "Indexed At", "Discovery Query",
    "Research Type", "Fact Status", "Review Status", "Notes",
    "Discovery Priority Score", "Discovery Priority Reasons", "Collected At (UTC)", "Collection Method",
]


def _article_type_hint(title: str, domain: str) -> str:
    """Heuristic triage only; never treats the outlet/title as proof."""
    d = (domain or "").lower().strip().removeprefix("www.")
    t = (title or "").lower()
    if d == "rockstargames.com" or d.endswith(".rockstargames.com") or d == "take2games.com" or d.endswith(".take2games.com"):
        return "Potential official source — verify"
    if any(term in t for term in ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed")):
        return "Claim/speculation terms detected — verify"
    return "News/reporting candidate — verify"


def _priority_score_and_reasons(title: str, domain: str, date_text: str = "") -> Tuple[int, str]:
    """Transparent sorting heuristic. It is not an AI judgment or virality prediction."""
    t = (title or "").lower()
    d = (domain or "").lower().strip().removeprefix("www.")
    score = 35
    reasons: List[str] = []

    if "grand theft auto vi" in t or "grand theft auto 6" in t:
        score += 24; reasons.append("Strong GTA VI title match")
    elif "gta vi" in t:
        score += 22; reasons.append("Explicit GTA VI title match")
    elif "gta 6" in t:
        score += 18; reasons.append("GTA 6 title match")
    elif "rockstar" in t:
        score += 8; reasons.append("Rockstar-related headline")

    date_value = (date_text or "").strip()
    parsed = None
    for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            parsed = datetime.strptime(date_value, fmt).replace(tzinfo=timezone.utc)
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            from email.utils import parsedate_to_datetime
            parsed = parsedate_to_datetime(date_value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            parsed = parsed.astimezone(timezone.utc)
        except Exception:
            parsed = None
    if parsed is not None:
        age_hours = max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds() / 3600)
        if age_hours <= 24:
            score += 22; reasons.append("Date appears within 24 hours")
        elif age_hours <= 72:
            score += 15; reasons.append("Date appears within 3 days")
        elif age_hours <= 168:
            score += 8; reasons.append("Date appears within 7 days")
        else:
            reasons.append("Older than 7 days by supplied date")
    else:
        score += 3; reasons.append("Date unavailable; freshness is uncertain")

    strong_terms = ("official", "trailer", "gameplay", "release date", "release window", "confirmed", "launch", "pre-order", "preorder", "price", "map", "delay", "update", "rockstar games", "take-two")
    hits = [term for term in strong_terms if term in t]
    if hits:
        score += min(10, 3 + len(hits))
        reasons.append("Specific news terms: " + ", ".join(hits[:3]))

    official_domains = ("rockstargames.com", "take2games.com")
    established_outlets = ("reuters.com", "bbc.com", "ign.com", "gamespot.com", "eurogamer.net", "videogameschronicle.com", "polygon.com", "pcgamer.com", "kotaku.com", "theverge.com", "axios.com", "gamesindustry.biz")
    if any(d == x or d.endswith("." + x) for x in official_domains):
        score += 12; reasons.append("Official-domain candidate; still verify page")
    elif any(d == x or d.endswith("." + x) for x in established_outlets):
        score += 6; reasons.append("Known games/news outlet domain")

    speculation_terms = ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed", "fake", "hoax")
    found_speculation = [term for term in speculation_terms if term in t]
    if found_speculation:
        score -= 16; reasons.append("Caution terms: " + ", ".join(found_speculation[:3]))

    score = max(10, min(95, score))
    if not reasons:
        reasons.append("General GTA VI relevance; manual review needed")
    return score, "; ".join(reasons)


def _format_gdelt_date(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            continue
    return value


def _make_news_record(title: str, url: str, domain: str, indexed_at: str, provider: str) -> Dict[str, str]:
    """Normalize discovery metadata and assign a transparent, non-predictive triage score."""
    score, reasons = _priority_score_and_reasons(title, domain, indexed_at)
    return {
        "Title": title.strip(),
        "Source": (domain or "Unknown publisher").strip(),
        "Source URL": url.strip(),
        "Indexed At": indexed_at,
        "Research Type": _article_type_hint(title, domain),
        "Fact Status": "Unverified — headline/metadata only",
        "Review Status": "Needs Review",
        "Notes": (
            f"Discovered via {provider}. Headline and metadata are not evidence that a claim is true. "
            "Open the original publisher source, verify the publication date and corroborate important claims before scripting."
        ),
        "Discovery Priority Score": str(score),
        "Discovery Priority Reasons": reasons,
        "Collected At (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "Collection Method": provider,
    }


def _fetch_gdelt_news_once(query: str, timespan: str, max_records: int) -> List[Dict[str, str]]:
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": int(max_records),
        "timespan": timespan,
        "sort": "datedesc",
    }
    endpoint = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
    request = Request(endpoint, headers={
        "User-Agent": "Mozilla/5.0 (compatible; VicePlugHub/1.1; news research dashboard)",
        "Accept": "application/json,text/plain,*/*",
    })
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))

    if not isinstance(payload, dict):
        raise RuntimeError("GDELT returned an unexpected response format.")

    results: List[Dict[str, str]] = []
    seen = set()
    for item in payload.get("articles", []) or []:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or item.get("url_mobile") or "").strip()
        domain = str(item.get("domain") or "").strip()
        if not title or not url or not url.startswith(("https://", "http://")):
            continue
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(_make_news_record(
            title, url, domain,
            _format_gdelt_date(item.get("seendate") or item.get("date")),
            "GDELT news index",
        ))
    return results


def _fetch_google_news_rss(query: str, timespan: str, max_records: int) -> List[Dict[str, str]]:
    """Fallback discovery via Google News RSS when GDELT rate-limits or is unavailable.

    Google News RSS is a useful fallback but is not a formally documented public API;
    publisher links and dates should still be checked by a human.
    """
    # Convert GDELT time windows into Google News's commonly supported `when:` query.
    age = {"1d": "1d", "3d": "3d", "7d": "7d", "30d": "30d"}.get(timespan, "7d")
    rss_query = f"{query} when:{age}"
    params = {"q": rss_query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    endpoint = "https://news.google.com/rss/search?" + urlencode(params)
    request = Request(endpoint, headers={
        "User-Agent": "Mozilla/5.0 (compatible; VicePlugHub/1.1; news research dashboard)",
        "Accept": "application/rss+xml,application/xml,text/xml,*/*",
    })
    with urlopen(request, timeout=20) as response:
        xml_bytes = response.read()

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise RuntimeError("Google News returned an unreadable RSS response.") from exc

    results: List[Dict[str, str]] = []
    seen = set()
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_node = item.find("source")
        source_name = (source_node.text or "").strip() if source_node is not None else ""
        source_url = source_node.attrib.get("url", "") if source_node is not None else ""
        domain = urlparse(source_url).netloc.lower().removeprefix("www.") if source_url else ""
        if not domain and url:
            domain = urlparse(url).netloc.lower().removeprefix("www.")
        if not title or not url or not url.startswith(("https://", "http://")):
            continue
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        display_source = domain or source_name or "Google News result"
        results.append(_make_news_record(
            title, url, display_source, pub_date,
            "Google News RSS fallback (GDELT was rate-limited/unavailable)",
        ))
        if len(results) >= max_records:
            break
    return results


@st.cache_data(ttl=900, show_spinner=False)
def fetch_gdelt_news(query: str, timespan: str, max_records: int) -> List[Dict[str, str]]:
    """Search GDELT first; fall back to Google News RSS on rate limits or outages.

    Results are headlines/source metadata only and are never treated as verified facts.
    Successful results are cached for 15 minutes to reduce repeat requests.
    """
    try:
        return _fetch_gdelt_news_once(query, timespan, max_records)
    except HTTPError as exc:
        if exc.code != 429:
            gdelt_error = f"GDELT returned HTTP {exc.code}: {exc.reason}"
        else:
            retry_after = (exc.headers.get("Retry-After", "") if exc.headers else "").strip()
            wait_note = f" Retry-After: {retry_after} seconds." if retry_after.isdigit() else ""
            gdelt_error = "GDELT rate-limited this request (HTTP 429)." + wait_note
    except (URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        gdelt_error = f"GDELT unavailable: {exc}"
    except Exception as exc:
        gdelt_error = f"GDELT request failed: {exc}"

    # Avoid retrying GDELT immediately after a 429. Use a separate source as fallback.
    try:
        rss_results = _fetch_google_news_rss(query, timespan, max_records)
        if rss_results:
            return rss_results
        raise RuntimeError("Google News RSS returned no matching articles.")
    except Exception as rss_exc:
        raise RuntimeError(
            f"{gdelt_error} Google News RSS fallback also failed: {rss_exc}. "
            "Try again later or use a narrower query; repeated retries can trigger further rate limits."
        ) from rss_exc


def _load_named_worksheet_records(worksheet_name: str) -> Tuple[pd.DataFrame, Any, str, str]:
    """Load a named worksheet without changing the existing Video Discovery source."""
    try:
        book = open_spreadsheet()
        try:
            ws = book.worksheet(worksheet_name)
        except Exception:
            return pd.DataFrame(), None, f"The '{worksheet_name}' worksheet has not been created yet. Save selected discoveries to create it.", "missing_tab"
        values = ws.get_all_values()
        if not values:
            return pd.DataFrame(), ws, f"Connected to {book.title} / {worksheet_name}, but the worksheet is empty.", "empty"
        headers = [str(h).strip() for h in values[0]]
        if not any(headers):
            return pd.DataFrame(), ws, f"The first row of {worksheet_name} must contain column headers.", "empty"
        seen: Dict[str, int] = {}
        clean_headers = []
        for i, name in enumerate(headers):
            base = name or f"Column {i + 1}"
            seen[base] = seen.get(base, 0) + 1
            clean_headers.append(base if seen[base] == 1 else f"{base} ({seen[base]})")
        width = len(clean_headers)
        rows = [(row + [""] * max(0, width - len(row)))[:width] for row in values[1:]]
        out = pd.DataFrame(rows, columns=clean_headers)
        out.insert(0, "_sheet_row", range(2, len(out) + 2))
        if len(out):
            visible = [c for c in out.columns if c != "_sheet_row"]
            nonempty = out[visible].astype(str).apply(lambda r: any(v.strip() for v in r), axis=1)
            out = out.loc[nonempty].reset_index(drop=True)
        return out, ws, f"Connected: {book.title} → {worksheet_name} · {len(out)} saved research items", "connected"
    except Exception as exc:
        return pd.DataFrame(), None, str(exc), "error"


def save_news_to_research_sheet(articles: List[Dict[str, str]], discovery_query: str) -> Tuple[int, int, str]:
    """Explicitly create/use the Research Feed worksheet and append only non-duplicates."""
    if not articles:
        return 0, 0, "No articles were selected."
    if not HAS_GSPREAD:
        raise RuntimeError("Google Sheets integration is unavailable. Add gspread and google-auth to requirements.txt.")
    book = open_spreadsheet()
    try:
        ws = book.worksheet(NEWS_WORKSHEET_NAME)
    except Exception:
        ws = book.add_worksheet(title=NEWS_WORKSHEET_NAME, rows=max(1000, len(articles) + 10), cols=len(NEWS_BASE_HEADERS) + 2)
        ws.update("A1", [NEWS_BASE_HEADERS])

    existing_values = ws.get_all_values()
    headers = [str(h).strip() for h in (existing_values[0] if existing_values else [])]
    if not any(headers):
        headers = NEWS_BASE_HEADERS.copy()
        ws.update("A1", [headers])
        existing_values = [headers]

    def col_for(names: List[str]) -> Optional[int]:
        normalized = [h.strip().lower() for h in headers]
        for name in names:
            if name.lower() in normalized:
                return normalized.index(name.lower())
        for name in sorted(names, key=len, reverse=True):
            for idx, header in enumerate(normalized):
                if name.lower() in header:
                    return idx
        return None

    # Add missing fields after the user's existing columns; never rename or replace their fields.
    required = [
        ("Title", ["title", "story title", "headline", "article title", "video title"]),
        ("Source", ["source", "publisher", "domain", "site"]),
        ("Source URL", ["source url", "article url", "source link", "url", "link"]),
        ("Indexed At", ["indexed at", "seen at", "published at", "published date", "publication date", "date published", "published", "date"]),
        ("Discovery Query", ["discovery query", "search query", "query"]),
        ("Research Type", ["research type", "source type"]),
        ("Fact Status", ["fact status", "verification status"]),
        ("Review Status", ["review status", "pipeline status", "content status", "status"]),
        ("Notes", ["notes", "research notes", "editor notes"]),
        ("Discovery Priority Score", ["discovery priority score", "triage score", "discovery score"]),
        ("Discovery Priority Reasons", ["discovery priority reasons", "priority reasons", "score reasons"]),
        ("Collected At (UTC)", ["collected at (utc)", "collected at", "automation timestamp"]),
        ("Collection Method", ["collection method", "discovery provider", "provider"]),
    ]
    missing_required = [(canonical, aliases) for canonical, aliases in required if col_for(aliases) is None]
    if missing_required:
        ensure_worksheet_capacity(ws, min_cols=len(headers) + len(missing_required))
        for canonical, aliases in missing_required:
            next_col = len(headers) + 1
            ws.update_cell(1, next_col, canonical)
            headers.append(canonical)

    # Refresh all current values after adding headers; dedupe by URL and title.
    existing_values = ws.get_all_values()
    url_idx = col_for(["source url", "article url", "source link", "url", "link"])
    title_idx = col_for(["title", "story title", "headline", "article title", "video title"])
    existing_urls, existing_titles = set(), set()
    for row in existing_values[1:]:
        if url_idx is not None and len(row) > url_idx and row[url_idx].strip():
            existing_urls.add(row[url_idx].strip().rstrip("/").lower())
        if title_idx is not None and len(row) > title_idx and row[title_idx].strip():
            existing_titles.add(row[title_idx].strip().lower())

    out_rows: List[List[str]] = []
    skipped = 0
    for article in articles:
        url = article.get("Source URL", "").strip()
        title = article.get("Title", "").strip()
        if (url and url.rstrip("/").lower() in existing_urls) or (title and title.lower() in existing_titles):
            skipped += 1
            continue
        row = [""] * len(headers)
        values_by_canonical = {
            "Title": title, "Source": article.get("Source", ""), "Source URL": url,
            "Indexed At": article.get("Indexed At", ""), "Discovery Query": discovery_query,
            "Research Type": article.get("Research Type", ""), "Fact Status": "Unverified — headline/metadata only",
            "Review Status": "Needs Review", "Notes": article.get("Notes", ""),
            "Discovery Priority Score": article.get("Discovery Priority Score", ""),
            "Discovery Priority Reasons": article.get("Discovery Priority Reasons", ""),
            "Collected At (UTC)": article.get("Collected At (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
            "Collection Method": article.get("Collection Method", "On-demand discovery"),
        }
        for canonical, aliases in required:
            idx = col_for(aliases)
            if idx is not None and idx < len(row):
                row[idx] = values_by_canonical.get(canonical, "")
        out_rows.append(row)
        if url: existing_urls.add(url.rstrip("/").lower())
        if title: existing_titles.add(title.lower())

    if out_rows:
        ensure_worksheet_capacity(ws, min_rows=len(existing_values) + len(out_rows), min_cols=len(headers))
        ws.append_rows(out_rows, value_input_option="USER_ENTERED")
    return len(out_rows), skipped, f"Saved to {book.title} → {NEWS_WORKSHEET_NAME}."

# -----------------------------------------------------------------------------
# Load records and build the shared application shell
# -----------------------------------------------------------------------------
df, worksheet, sheet_message, sheet_status = load_sheet_records()

# Hero only appears on Dashboard, not at the top of every workspace.
if st.session_state.active_tab == "Dashboard":
    st.markdown("""
    <section class="vp-hero">
      <div class="vp-hero-copy">
        <div class="vp-hero-topline"><span class="vp-live-dot"></span> VICE CITY INTELLIGENCE / CREATOR TERMINAL</div>
        <h1>STAY AHEAD OF<br><span>VICE CITY.</span></h1>
        <p>Your GTA VI research command center. Discover new coverage, prioritize leads, develop Shorts scripts, and move ideas through review—with the original source always in reach.</p>
        <div class="vp-hero-tags"><span>RESEARCH</span><span>VERIFY</span><span>CREATE</span><span>PUBLISH</span></div>
      </div>
      <div class="vp-hero-art" aria-hidden="true">
        <div class="vp-hero-code top">VP / INTEL UNIT 06</div>
        <div class="vp-orbit vp-orbit-one"></div><div class="vp-orbit vp-orbit-two"></div><div class="vp-orbit vp-orbit-three"></div>
        <div class="vp-hero-core">VP</div>
        <div class="vp-hero-code bottom">VICEPLUG HUB • 2026</div>
      </div>
    </section>
    """, unsafe_allow_html=True)

col_nav, col_main = st.columns([1.0, 5.6], gap="large")
with col_nav:
    st.markdown('''<div class="vp-logo-lockup"><div class="vp-logo-mark">VP</div><div><div class="vp-brand">VICE<span>PLUG</span> HUB</div><div class="vp-logo-sub">GTA VI CONTENT INTEL</div></div></div>''', unsafe_allow_html=True)
    nav_groups = {
        "Dashboard": "OVERVIEW",
        "Research Feed": "DISCOVER",
        "Viral Opportunities": "DISCOVER",
        "Video Discovery": "DISCOVER",
        "AI Studio": "CREATE",
        "Script Generator": "CREATE",
        "Content Pipeline": "WORKFLOW",
        "Review Queue": "WORKFLOW",
        "Trends & Analytics": "INSIGHTS",
        "Google Sheets Sync": "SYSTEM",
        "Settings": "SYSTEM",
    }
    last_group = None
    for label, icon in NAV_ITEMS:
        group = nav_groups.get(label, "WORKSPACE")
        if group != last_group:
            st.markdown(f'<div class="vp-nav-group">{html.escape(group)}</div>', unsafe_allow_html=True)
            last_group = group
        is_active = st.session_state.active_tab == label
        button_label = f"{icon}  {label}"
        if st.button(button_label, key=f"nav_{label}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.active_tab = label
            st.rerun()
    st.markdown('<div class="vp-nav-foot">GOOD CONTENT<br><b style="color:#b8c4da">BUILDS BIGGER WORLDS.</b><br><span style="color:#586780">RESEARCH → VERIFY → CREATE</span></div>', unsafe_allow_html=True)

with col_main:
    # =====================================================================
    # DASHBOARD
    # =====================================================================
    if st.session_state.active_tab == "Dashboard":
        greet_left, greet_right = st.columns([1.4, 1])
        with greet_left:
            st.markdown('<div class="vp-page-head" style="border:0;margin-bottom:.5rem;padding-bottom:0"><div><h1 style="font-size:1.55rem">Welcome back, Creator.</h1><p>Your GTA VI research and content overview.</p></div></div>', unsafe_allow_html=True)
        with greet_right:
            st.markdown(f'<div style="text-align:right;color:#91a3bd;font-size:.76rem;padding-top:8px">{datetime.now().strftime("%A, %B %d, %Y")}<br><span style="color:{"#10b981" if sheet_status == "connected" else "#f59e0b"};font-weight:700">● {"Google Sheets connected" if sheet_status == "connected" else "Google Sheets not connected"}</span></div>', unsafe_allow_html=True)

        title_col = title_column(df) if not df.empty else None
        score_col = score_column(df) if not df.empty else None
        status_col = status_column(df) if not df.empty else None
        scores = df[score_col].apply(number_value).dropna() if score_col else pd.Series(dtype=float)
        statuses = df[status_col].fillna("").astype(str).str.lower() if status_col else pd.Series(dtype=str)
        pending_count = int(statuses.str.contains("review|pending|needs approval|needs review", regex=True).sum()) if len(statuses) else 0
        approved_count = int(statuses.str.contains("approved|published", regex=True).sum()) if len(statuses) else 0
        stories_count = int(len(df))
        avg_score = f"{scores.mean():.0f}/100" if len(scores) else "—"
        metrics = st.columns(5, gap="large")
        with metrics[0]: metric_card("Research Records", str(stories_count), "Rows loaded from your sheet" if sheet_status == "connected" else "Connect Sheets for live counts", "📰", "#ff2e93")
        with metrics[1]: metric_card("Scored Ideas", str(int(len(scores))), "Records with a numeric score", "🎯", "#38d9f5")
        with metrics[2]: metric_card("Average Score", avg_score, "Based on available score fields", "⭐", "#a855f7")
        with metrics[3]: metric_card("Needs Review", str(pending_count) if status_col else "—", "Based on your status column", "🧾", "#f43f5e")
        with metrics[4]: metric_card("Approved / Published", str(approved_count) if status_col else "—", "Based on your status column", "✅", "#10b981")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        main_col, side_col = st.columns([1.5, 1], gap="large")
        with main_col:
            st.markdown('<div class="vp-panel"><div class="vp-panel-title">🔥 Top Research Opportunities</div><div class="vp-muted">Ranked using the score already stored in your sheet. A score is a prioritization estimate, not a promise of virality.</div></div>', unsafe_allow_html=True)
            if df.empty or not title_col:
                show_missing_data(sheet_message if sheet_status != "connected" else "Add a title column and research records to your worksheet.")
            else:
                best = sorted_by_score(df).head(5)
                render_record_cards(best, key_prefix="dashboard_top_opportunities", max_items=5, columns_count=1)
        with side_col:
            st.markdown('<div class="vp-panel"><div class="vp-panel-title">⚡ Content Pipeline</div><div class="vp-muted">Progress inferred from your sheet status column.</div></div>', unsafe_allow_html=True)
            if not status_col:
                st.info("Your worksheet does not appear to have a Review Status or Status column, so pipeline counts are unavailable.")
            else:
                pipeline_stages = [
                    ("Research", len(df), "#38d9f5"),
                    ("Needs Review", int(statuses.str.contains("review|pending|needs", regex=True).sum()), "#f59e0b"),
                    ("Approved", int(statuses.str.contains("approved", regex=True).sum()), "#10b981"),
                    ("Published", int(statuses.str.contains("published", regex=True).sum()), "#a855f7"),
                ]
                for stage, count, color in pipeline_stages:
                    st.markdown(f'<div style="display:flex;justify-content:space-between;gap:10px;padding:12px 2px;border-bottom:1px solid #1a263b"><span style="color:#cbd5e1">● &nbsp;{stage}</span><b style="color:{color}">{count}</b></div>', unsafe_allow_html=True)
            st.markdown('<div class="vp-panel" style="margin-top:12px"><div class="vp-panel-title">🧠 Quick Actions</div></div>', unsafe_allow_html=True)
            quick1, quick2 = st.columns(2)
            with quick1:
                if st.button("Open AI Studio", use_container_width=True):
                    st.session_state.active_tab = "AI Studio"; st.rerun()
            with quick2:
                if st.button("Review Queue", use_container_width=True):
                    st.session_state.active_tab = "Review Queue"; st.rerun()
        st.markdown('<div class="vp-panel" style="margin-top:10px"><span class="vp-pill">DATA NOTE</span><div class="vp-muted" style="margin-top:8px">The dashboard no longer invents trend counts, view totals, confidence percentages, or breaking-news headlines. Figures appear only when the connected worksheet contains the relevant data.</div><div class="vp-muted" style="margin-top:8px">Automated collection is performed by the optional GitHub Actions workflow, not by keeping this Streamlit page open. Research Feed items receive transparent heuristic priority scores and still require source verification.</div></div>', unsafe_allow_html=True)

    # =====================================================================
    # RESEARCH FEED / VIDEO DISCOVERY
    # =====================================================================
    elif st.session_state.active_tab == "Research Feed":
        render_page_header("Research Feed", "Discover recent GTA VI coverage from public news metadata, then choose what to save for human review.")
        st.markdown('<div class="vp-panel"><div class="vp-panel-title">🌐 Live & scheduled News Discovery</div><div class="vp-muted">On-demand search tries GDELT first and falls back to Google News RSS when needed. The optional GitHub Actions collector can search the RSS feed twice daily and save new items to this same worksheet. Both workflows add a transparent discovery priority score; headlines remain unverified leads, not confirmed facts.</div></div>', unsafe_allow_html=True)
        search_left, search_right = st.columns([2.2, 1])
        with search_left:
            discovery_query = st.text_input("Search query", value=st.session_state.get("news_query", NEWS_DEFAULT_QUERY), key="news_query_input", help='Try a phrase, e.g. \"GTA VI\" OR Rockstar OR \"Grand Theft Auto 6\"')
        with search_right:
            timespan_label = st.selectbox("Coverage window", ["Past 24 hours", "Past 3 days", "Past 7 days", "Past 30 days"], index=2, key="news_timespan_label")
        timespan = {"Past 24 hours": "1d", "Past 3 days": "3d", "Past 7 days": "7d", "Past 30 days": "30d"}[timespan_label]
        result_limit = st.slider("Maximum results", min_value=5, max_value=100, value=25, step=1, key="news_result_limit", help="Choose any count from 5 to 100 using one-result increments.")
        if st.button("🔎 Search fresh coverage", type="primary", use_container_width=True):
            if not discovery_query.strip():
                st.warning("Enter a search query.")
            else:
                try:
                    with st.spinner("Searching recent news metadata…"):
                        found = fetch_gdelt_news(discovery_query.strip(), timespan, result_limit)
                    previous_found = st.session_state.get("news_discovery_results", [])
                    for i in range(len(previous_found)):
                        st.session_state.pop(f"news_discovery_pick_{i}", None)
                    st.session_state.news_discovery_results = found
                    st.session_state.news_discovery_query = discovery_query.strip()
                    st.session_state.news_discovery_error = ""
                    st.success(f"Found {len(found)} candidate articles. Review the original sources before using any claim.")
                except Exception as exc:
                    previous_found = st.session_state.get("news_discovery_results", [])
                    for i in range(len(previous_found)):
                        st.session_state.pop(f"news_discovery_pick_{i}", None)
                    st.session_state.news_discovery_error = str(exc)
                    st.session_state.news_discovery_results = []
        if st.session_state.get("news_discovery_error"):
            st.error(st.session_state.news_discovery_error)
        found = st.session_state.get("news_discovery_results", [])
        if found:
            st.markdown("### Discovery results")
            st.caption("Choose individual stories to save. Duplicate links and titles already in Research Feed will be skipped.")
            selected_positions = []
            for offset in range(0, len(found), 2):
                slots = st.columns(2, gap="large")
                for local_i, item in enumerate(found[offset:offset + 2]):
                    position = offset + local_i
                    with slots[local_i]:
                        title = safe_text(item.get("Title", "Untitled story"), 230)
                        source = safe_text(item.get("Source", "Publisher not recorded"), 85)
                        indexed_at = safe_text(item.get("Indexed At", "Date not recorded"), 55)
                        triage = safe_text(item.get("Research Type", "Needs verification"), 50)
                        score_val = number_value(item.get("Discovery Priority Score", ""))
                        score_chip = f'<span class="vp-record-score">{score_val:.0f}<span style="opacity:.7">/100</span></span>' if score_val is not None else '<span class="vp-record-kicker">UNSCORED</span>'
                        reasons = safe_text(item.get("Discovery Priority Reasons", "No prioritization explanation was provided."), 320)
                        source_url = str(item.get("Source URL", "") or "").strip()
                        source_link = f'<a href="{html.escape(source_url, quote=True)}" target="_blank" rel="noopener noreferrer">Open original source ↗</a>' if source_url.startswith(("https://", "http://")) else '<span>No source URL saved</span>'
                        st.markdown(f'''<article class="vp-record-card">
                          <div class="vp-record-top"><span class="vp-record-kicker">NEW DISCOVERY · {position + 1:02d}</span>{score_chip}</div>
                          <h3>{title}</h3>
                          <p class="vp-record-summary">{reasons}</p>
                          <div class="vp-record-chips"><span class="vp-record-chip">◈ {source}</span><span class="vp-record-chip fact">{triage}</span><span class="vp-record-chip status">Unverified lead</span></div>
                          <div class="vp-record-meta"><span>◷ {indexed_at}</span><span>Review before scripting</span></div>
                          <div class="vp-record-footer">{source_link}<span>News metadata</span></div>
                        </article>''', unsafe_allow_html=True)
                        checked = st.checkbox("Select this story to save", key=f"news_discovery_pick_{position}")
                        if checked:
                            selected_positions.append(position)
            save_col, clear_col = st.columns([2, 1], gap="large")
            with save_col:
                if st.button(f"💾 Save {len(selected_positions)} selected stories to Google Sheets", type="primary", use_container_width=True, disabled=not selected_positions):
                    try:
                        selected_articles = [found[i] for i in selected_positions]
                        with st.spinner("Saving selected discovery records…"):
                            saved_count, skipped_count, message = save_news_to_research_sheet(selected_articles, st.session_state.get("news_discovery_query", discovery_query.strip()))
                        st.success(f"{message} Added {saved_count}; skipped {skipped_count} duplicate(s).")
                        for i in range(len(found)):
                            st.session_state.pop(f"news_discovery_pick_{i}", None)
                        st.session_state.news_discovery_results = []
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save discoveries: {exc}")
            with clear_col:
                if st.button("Clear results", use_container_width=True):
                    for i in range(len(found)):
                        st.session_state.pop(f"news_discovery_pick_{i}", None)
                    st.session_state.news_discovery_results = []
                    st.rerun()
        else:
            st.markdown('<div class="vp-empty"><b>No discovery results yet</b><br><span>Run a search to find recently indexed GTA VI headlines and publisher links.</span></div>', unsafe_allow_html=True)

        st.markdown("### Saved Research Feed")
        news_df, news_ws, news_message, news_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
        if news_status == "connected" and not news_df.empty:
            st.success(news_message)
            saved_title_col = title_column(news_df)
            saved_query = st.text_input("Filter saved research", placeholder="Filter headlines or publishers…", key="saved_news_filter")
            saved_view = news_df.copy()
            if saved_query.strip():
                saved_view = saved_view[saved_view.astype(str).apply(lambda col: col.str.contains(saved_query.strip(), case=False, na=False)).any(axis=1)]
            saved_score_col = score_column(saved_view)
            if saved_score_col:
                saved_view = sorted_by_score(saved_view)
                saved_view = saved_view.drop(columns=["_numeric_score"], errors="ignore")
            render_record_cards(saved_view, key_prefix="saved_news_cards", max_items=40, columns_count=2, show_raw_expander=True)
            if saved_score_col:
                st.caption(f"Sorted by {saved_score_col}. This is a sorting heuristic, not a fact-check or view prediction.")
        else:
            st.info(news_message or f"No saved Research Feed worksheet yet. Select results above and save them to create '{NEWS_WORKSHEET_NAME}'.")
        st.caption("Discovery providers: GDELT Project, with Google News RSS as an automatic fallback. The date may be a publisher publication date or an index timestamp, depending on the provider. Headlines and metadata are leads only; verify the original publisher source before using claims in a script. Google News RSS is an unofficial feed endpoint and may change.")

    # =====================================================================
    # VIDEO DISCOVERY — existing Google Sheets video workflow
    # =====================================================================
    elif st.session_state.active_tab == "Video Discovery":
        page_title = "Video Discovery"
        render_page_header(page_title, "Search and inspect video records already collected in your Google Sheet.")
        if df.empty:
            show_missing_data(sheet_message)
        else:
            query = st.text_input("Search video records", placeholder="Search titles, source links, summaries…", key="search_video_discovery")
            view = df.copy()
            if query.strip():
                mask = view.astype(str).apply(lambda c: c.str.contains(query.strip(), case=False, na=False)).any(axis=1)
                view = view[mask]
            st.markdown(f'<div class="vp-panel"><div class="vp-panel-title">Your video research library</div><div class="vp-muted">{len(view)} records match the current search. Each card keeps the source and review context close to the title.</div></div>', unsafe_allow_html=True)
            if not title_column(view):
                st.warning("No title-like column was detected. Showing the records with available fields.")
            render_record_cards(view, key_prefix="video_discovery_cards", max_items=40, columns_count=2, show_raw_expander=True)

    # =====================================================================
    # VIRAL OPPORTUNITIES
    # =====================================================================
    elif st.session_state.active_tab == "Viral Opportunities":
        render_page_header("Viral Opportunities", "Rank research leads with transparent prioritization signals; scores do not predict views or verify facts.")
        opportunity_source = st.radio("Rank records from", ["Research Feed", "Video Discovery"], horizontal=True, key="opportunity_source")
        if opportunity_source == "Research Feed":
            opp_df, opp_ws, opp_message, opp_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
        else:
            opp_df, opp_ws, opp_message, opp_status = df, worksheet, sheet_message, sheet_status
        if opp_df.empty:
            show_missing_data(opp_message)
        elif not score_column(opp_df):
            st.info("No score column was detected. For Research Feed items, run a fresh search or the scheduled collector to populate Discovery Priority Score. Records are still shown as cards below.")
            render_record_cards(opp_df, key_prefix="opportunities_unscored", max_items=40, columns_count=2, show_raw_expander=True)
        else:
            opp_score_col = score_column(opp_df)
            min_score = st.slider("Minimum priority score", 0, 100, 45, key=f"minimum_priority_{opportunity_source}")
            ranked = sorted_by_score(opp_df)
            ranked = ranked[ranked["_numeric_score"].fillna(-1) >= min_score]
            st.caption(f"Showing {len(ranked)} records scoring {min_score}+ from {opportunity_source}. Scores use metadata heuristics or saved AI analysis, depending on the selected field.")
            render_record_cards(ranked.drop(columns=["_numeric_score"], errors="ignore"), key_prefix=f"opportunities_{opportunity_source}", max_items=40, columns_count=2, show_raw_expander=True)
            st.info("The discovery score is a transparent sorting aid based on headline match, apparent freshness, selected source-domain signals and caution terms. It is not an estimate of views, truth, or virality. Verify the publisher and claims yourself.")

    # =====================================================================
    # AI STUDIO — analyze existing record
    # =====================================================================
    elif st.session_state.active_tab == "AI Studio":
        render_page_header("AI Studio", "Turn a saved video or news research record into an evidence-aware content brief.")
        ai_source = st.radio("Analyze records from", ["Video Discovery", "Research Feed"], horizontal=True, key="ai_studio_source")
        if ai_source == "Research Feed":
            analysis_df, analysis_ws, analysis_message, analysis_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
            analysis_sheet_name = NEWS_WORKSHEET_NAME
        else:
            analysis_df, analysis_ws, analysis_message, analysis_status = df, worksheet, sheet_message, sheet_status
            analysis_sheet_name = analysis_ws.title if analysis_ws is not None else str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))

        if analysis_df.empty or not title_column(analysis_df):
            show_missing_data(analysis_message if analysis_status != "connected" else "Add records with a Title column to analyze them here.")
        else:
            tcol = title_column(analysis_df)
            selected_idx = st.selectbox("Choose a research record", analysis_df.index.tolist(), format_func=lambda idx: str(analysis_df.loc[idx, tcol])[:130], key=f"ai_record_{ai_source}")
            selected_record = analysis_df.loc[selected_idx]
            sheet_row = int(selected_record.get("_sheet_row", selected_idx + 2))
            record = selected_record.drop(labels=["_sheet_row"], errors="ignore").to_dict()
            with st.expander("Source fields sent to the AI", expanded=False):
                st.json({k: str(v)[:1200] for k, v in record.items()})
            st.warning("Groq analyzes the saved title and fields only. It does not watch videos or independently verify article claims. Review the original source before using any factual statement.")
            if st.button("✨ Analyze selected record with Groq", type="primary", use_container_width=True, key="analyze_selected_ai_record"):
                system_prompt = """You are VicePlug Hub's GTA VI research editor. Use only information in the supplied record. Never invent gameplay, trailer frames, patents, leaks, release dates, view counts, or quotes. If the record lacks evidence, state that clearly. Distinguish official information, reputable reporting, creator commentary, speculation, and unverified claims. Return one JSON object with keys: relevance (High/Medium/Low), priority_score (1-100), fact_status, summary, why_it_matters, hook, commentary_draft (20-35 seconds), on_screen_text, title, caption, hashtags (array), verification_needed (array), rights_note, recommended_action. A score is only a prioritization estimate, not a prediction of virality."""
                user_prompt = "Analyze this saved research record. Treat all fields as unverified unless the source field itself clearly establishes provenance. Do not infer that a claim is true simply because it appears in a headline.\n\n" + json.dumps(record, ensure_ascii=False, default=str)
                try:
                    with st.spinner("Preparing the content brief…"):
                        result = call_groq(system_prompt, user_prompt, max_tokens=1900)
                    st.session_state.generated_ai_brief = result
                    st.session_state.generated_ai_source = ai_source
                    st.session_state.generated_ai_row = sheet_row
                    st.session_state.generated_ai_sheet = analysis_sheet_name
                    st.success("Draft generated. Verify every factual claim and source before using it.")
                except Exception as exc:
                    st.error(f"AI analysis failed: {exc}")

            brief = st.session_state.get("generated_ai_brief")
            same_record = (st.session_state.get("generated_ai_source") == ai_source and
                           st.session_state.get("generated_ai_row") == sheet_row and
                           st.session_state.get("generated_ai_sheet") == analysis_sheet_name)
            if brief and same_record:
                st.markdown("### Generated content brief")
                render_generated_brief(brief, mode="AI analysis brief")
                st.download_button("Download brief as JSON", data=json.dumps(brief, ensure_ascii=False, indent=2), file_name="viceplug_ai_brief.json", mime="application/json", use_container_width=True, key="download_ai_brief")
                if st.button("💾 Save AI brief to this Google Sheets record", type="primary", use_container_width=True, key="save_ai_brief_to_sheet"):
                    try:
                        with st.spinner("Saving AI fields to the selected research row…"):
                            saved_message = save_ai_brief_to_worksheet(analysis_sheet_name, sheet_row, brief)
                        st.success(saved_message)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save the AI brief: {exc}")

    # =====================================================================
    # SCRIPT GENERATOR
    # =====================================================================
    elif st.session_state.active_tab == "Script Generator":
        render_page_header("Script Generator", "Draft a short-form script from a topic and evidence you provide.")
        st.markdown('<div class="vp-panel"><div class="vp-panel-title">Create a Short concept</div><div class="vp-muted">The generator should not make up details to make a story sound more exciting. Add source facts and a URL when available.</div></div>', unsafe_allow_html=True)
        topic = st.text_input("Video opportunity topic", placeholder="e.g. A confirmed detail from an official GTA VI trailer", key="script_topic")
        source_url = st.text_input("Source URL (optional)", placeholder="https://…", key="script_source_url")
        evidence = st.text_area("Verified facts / source notes", placeholder="Paste the facts that the script is allowed to state. Separate confirmed details from speculation.", height=130, key="script_evidence")
        angle = st.selectbox("Content angle", ["Explain a confirmed detail", "Compare GTA V and GTA VI", "Summarize reputable reporting", "Explore a clearly labelled theory", "React to creator commentary"])
        length = st.select_slider("Target length", options=[15, 20, 30, 40, 50, 60], value=30, format_func=lambda v: f"{v} seconds")
        if st.button("✨ Generate script with Groq", type="primary", use_container_width=True):
            if not topic.strip():
                st.warning("Enter a topic first.")
            elif not evidence.strip():
                st.warning("Add source facts or notes first. Without evidence, the script may only discuss the topic as an unverified idea.")
            else:
                system_prompt = """You write engaging short-form gaming scripts for VicePlug Hub. Use only supplied evidence. Do not invent events, trailer details, quotes, patents, leaks, release timing, numbers, or claims about what Rockstar confirmed. Label speculation. If evidence is insufficient, say so in verification_needed and avoid stating the claim as fact. Return JSON only with keys: title, spoken_hook, voiceover_script, timestamped_beats (array of objects with start, end, narration, visual_direction), on_screen_text (array), caption, hashtags (array), verification_needed (array), rights_note, why_this_angle. Make it punchy but accurate. Do not claim to have watched a source."""
                user_prompt = json.dumps({"topic": topic, "source_url": source_url, "evidence": evidence, "angle": angle, "target_seconds": length, "platforms": ["YouTube Shorts", "TikTok"]}, ensure_ascii=False)
                try:
                    with st.spinner("Drafting the script and on-screen beats…"):
                        result = call_groq(system_prompt, user_prompt, max_tokens=2200)
                    st.session_state.generated_script = result
                    st.success("Script draft generated. Review sources, edit it, and approve before publishing.")
                except Exception as exc:
                    st.error(f"Script generation failed: {exc}")
        if st.session_state.generated_script:
            st.markdown("### Your generated draft")
            result = st.session_state.generated_script
            render_generated_brief(result, mode="Script studio draft")
            st.download_button("Download script brief", data=json.dumps(result, ensure_ascii=False, indent=2), file_name="viceplug_script_draft.json", mime="application/json", use_container_width=True)

    # =====================================================================
    # CONTENT PIPELINE / REVIEW QUEUE
    # =====================================================================
    elif st.session_state.active_tab in ["Content Pipeline", "Review Queue"]:
        if st.session_state.active_tab == "Content Pipeline":
            render_page_header("Content Pipeline", "Track research records from discovery through review and publication.")
        else:
            render_page_header("Review Queue", "Focus on records that still need human review or approval.")

        pipeline_source = st.radio("Review records from", ["Video Discovery", "Research Feed"], horizontal=True, key=f"pipeline_source_{st.session_state.active_tab}")
        if pipeline_source == "Research Feed":
            pipeline_df, pipeline_ws, pipeline_message, pipeline_connection = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
            pipeline_sheet_name = NEWS_WORKSHEET_NAME
        else:
            pipeline_df, pipeline_ws, pipeline_message, pipeline_connection = df, worksheet, sheet_message, sheet_status
            pipeline_sheet_name = pipeline_ws.title if pipeline_ws is not None else str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))

        if pipeline_df.empty:
            show_missing_data(pipeline_message)
        else:
            s_col = status_column(pipeline_df)
            if not s_col:
                st.warning(f"No Review Status / Status column was detected in {pipeline_sheet_name}. Add a status column to enable stage tracking.")
                render_record_cards(pipeline_df, key_prefix=f"pipeline_no_status_{pipeline_source}", max_items=40, columns_count=2, show_raw_expander=True)
            else:
                statuses = pipeline_df[s_col].fillna("").astype(str).str.strip()
                if st.session_state.active_tab == "Review Queue":
                    mask = statuses.str.lower().str.contains("review|pending|needs|draft|unreviewed", regex=True)
                    shown = pipeline_df[mask]
                else:
                    shown = pipeline_df.copy()
                stages = st.columns(4)
                labels = ["Needs Review", "Script Draft", "Approved", "Published"]
                patterns = ["review|pending|needs|unreviewed", "script|draft", "approved", "published"]
                for slot, label, pattern in zip(stages, labels, patterns):
                    count = int(statuses.str.lower().str.contains(pattern, regex=True).sum())
                    with slot:
                        st.markdown(f'<div class="vp-card"><div class="vp-metric-label">{label}</div><div class="vp-metric-value">{count}</div><div class="vp-metric-note">Matching status values</div></div>', unsafe_allow_html=True)
                st.markdown(" ")
                render_record_cards(shown, key_prefix=f"pipeline_{st.session_state.active_tab}_{pipeline_source}", max_items=40, columns_count=2, show_raw_expander=True)
                shown_title_col = title_column(shown)
                if len(shown):
                    record_index = st.selectbox("Select a record to update", shown.index.tolist(), format_func=lambda idx: str(shown.loc[idx, shown_title_col])[:120] if shown_title_col else f"Sheet row {shown.loc[idx, '_sheet_row']}", key=f"pipeline_record_{st.session_state.active_tab}_{pipeline_source}")
                    current_status = str(pipeline_df.loc[record_index, s_col]) or "Unspecified"
                    st.caption(f"Current status: {current_status}")
                    statuses_options = ["Needs Review", "Script Draft", "In Review", "Approved", "Ready to Edit", "Ready to Publish", "Published", "Rejected"]
                    default_status_idx = statuses_options.index(current_status) if current_status in statuses_options else 0
                    new_status = st.selectbox("New status", statuses_options, index=default_status_idx, key=f"new_pipeline_status_{pipeline_source}_{st.session_state.active_tab}")
                    if st.button("Save status to Google Sheets", type="primary", key=f"save_pipeline_status_{pipeline_source}_{st.session_state.active_tab}"):
                        if pipeline_ws is None or pipeline_connection != "connected":
                            st.error("Google Sheets is not connected, so the status was not saved.")
                        else:
                            actual_headers = [str(h).strip() for h in pipeline_ws.row_values(1)]
                            normalized = [h.lower() for h in actual_headers]
                            try:
                                status_index = next(i for i, h in enumerate(normalized) if h in ["review status", "pipeline status", "content status", "status"])
                                sheet_row = int(pipeline_df.loc[record_index, "_sheet_row"])
                                pipeline_ws.update_cell(sheet_row, status_index + 1, new_status)
                                st.success(f"Updated {pipeline_sheet_name}, row {sheet_row} to '{new_status}'.")
                                st.rerun()
                            except StopIteration:
                                st.error("Could not find a supported status header in row 1; nothing was changed.")
                            except Exception as exc:
                                st.error(f"Could not save status: {exc}")

    # =====================================================================
    # TRENDS & ANALYTICS — no invented analytics
    # =====================================================================
    elif st.session_state.active_tab == "Trends & Analytics":
        render_page_header("Trends & Analytics", "See only the trends supported by records and metrics you have actually collected.")
        if df.empty:
            show_missing_data(sheet_message)
        else:
            topic_col = first_matching_column(df, ["Topic", "Category", "Keyword", "Trend", "Content Pillar"])
            date_col = first_matching_column(df, ["Published At", "Date Published", "Date", "Created At", "Collected At", "Timestamp", "End Timestamp"])
            views_col = first_matching_column(df, ["Views", "View Count", "Views Count", "Video Views"])
            score_col = score_column(df)
            left, right = st.columns(2)
            with left:
                st.markdown('<div class="vp-panel"><div class="vp-panel-title">Score distribution</div><div class="vp-muted">Only numeric scores stored in the worksheet are included.</div></div>', unsafe_allow_html=True)
                if score_col:
                    chart_df = pd.DataFrame({"Priority score": df[score_col].apply(number_value).dropna()})
                    if len(chart_df):
                        st.bar_chart(chart_df["Priority score"].value_counts(bins=10, sort=False).sort_index())
                    else:
                        st.info("Score column exists, but contains no numeric scores yet.")
                else:
                    st.info("Add an AI Priority Score or Viral Score column to chart scores.")
            with right:
                st.markdown('<div class="vp-panel"><div class="vp-panel-title">Recorded views</div><div class="vp-muted">Not a prediction. This chart needs real view counts from your sheet.</div></div>', unsafe_allow_html=True)
                if views_col:
                    views = df[views_col].apply(number_value).dropna()
                    if len(views):
                        st.bar_chart(views.reset_index(drop=True).rename("Views"))
                    else:
                        st.info("View-count column exists, but there are no numeric values.")
                else:
                    st.info("No views column detected. Connect platform analytics before making performance claims.")
            if topic_col:
                st.markdown("### Most frequent recorded topics")
                counts = df[topic_col].fillna("").astype(str).str.strip()
                counts = counts[counts != ""].value_counts().head(10)
                if len(counts):
                    st.bar_chart(counts)
                else:
                    st.info("The topic/category column is empty.")
            else:
                st.info("Add a Topic, Category, Keyword, Trend, or Content Pillar column to analyze recurring subjects.")
            if date_col:
                st.caption(f"Date-like field detected: {date_col}. Date-based growth comparisons can be added once the values are consistently formatted.")

    # =====================================================================
    # GOOGLE SHEETS SYNC
    # =====================================================================
    elif st.session_state.active_tab == "Google Sheets Sync":
        render_page_header("Google Sheets Sync", "Inspect your connected research worksheet and check connection setup.")
        if sheet_status == "connected":
            st.success(sheet_message)
            st.caption("This screen reads your configured research worksheet. Status edits in Content Pipeline / Review Queue are written back when a supported status column exists.")
            render_record_cards(df, key_prefix="sheets_sync_cards", max_items=40, columns_count=2, show_raw_expander=True)
            if st.button("Refresh from Google Sheets", type="primary"):
                st.rerun()
        else:
            st.error("Google Sheets is not connected.")
            st.code("GOOGLE_SHEET_ID = \"your-spreadsheet-id\"\nGROQ_API_KEY = \"your-groq-key\"\n\n[gcp_service_account]\ntype = \"service_account\"\n... = \"your service account fields\"", language="toml")
            st.markdown("In Streamlit Community Cloud, add secrets under **App → Settings → Secrets**. Share the spreadsheet with the service-account email as an Editor. Do not paste API keys into this Python file or a public repository.")
            if sheet_message:
                with st.expander("Connection detail"):
                    st.code(sheet_message)

    # =====================================================================
    # SETTINGS
    # =====================================================================
    elif st.session_state.active_tab == "Settings":
        render_page_header("Settings & Integrations", "Review configuration without exposing your API keys.")
        groq_configured = bool(get_secret("GROQ_API_KEY"))
        account_configured = bool(get_service_account_info() or (get_secret("GOOGLE_SERVICE_ACCOUNT_FILE") and os.path.exists(str(get_secret("GOOGLE_SERVICE_ACCOUNT_FILE")))))
        settings = [
            ("Groq API", "Connected / key present" if groq_configured and HAS_GROQ else "Not configured" if not groq_configured else "Package missing", "#10b981" if groq_configured and HAS_GROQ else "#f59e0b"),
            ("Google Sheets", "Connected" if sheet_status == "connected" else "Not connected", "#10b981" if sheet_status == "connected" else "#f59e0b"),
            ("Spreadsheet credentials", "Configured" if account_configured else "Missing", "#10b981" if account_configured else "#f59e0b"),
            ("Groq model", str(get_secret("GROQ_MODEL", "openai/gpt-oss-20b")), "#38d9f5"),
            ("Research worksheet", str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery")), "#a855f7"),
            ("News research worksheet", NEWS_WORKSHEET_NAME, "#ff2e93"),
        ]
        for label, value, color in settings:
            st.markdown(f'<div class="vp-panel" style="display:flex;align-items:center;justify-content:space-between;gap:14px"><div style="font-weight:700">{html.escape(label)}</div><div style="color:{color};font-weight:700;text-align:right">{html.escape(value)}</div></div>', unsafe_allow_html=True)
        st.markdown("### Required Streamlit Secrets")
        st.code('GROQ_API_KEY = "your-groq-api-key"\nGROQ_MODEL = "openai/gpt-oss-20b"\nGOOGLE_SHEET_ID = "your-google-sheet-id"\nVIDEO_DISCOVERY_WORKSHEET = "Video Discovery"\nNEWS_RESEARCH_WORKSHEET = "Research Feed"\n\n[gcp_service_account]\ntype = "service_account"\nproject_id = "..."\nprivate_key_id = "..."\nprivate_key = "..."\nclient_email = "..."\nclient_id = "..."\nauth_uri = "https://accounts.google.com/o/oauth2/auth"\ntoken_uri = "https://oauth2.googleapis.com/token"\nauth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"\nclient_x509_cert_url = "..."', language="toml")
        st.caption("Use your actual service-account values in Streamlit Secrets; the example above is a template, not a working credential.")

# Footer in normal flow, inside the selected workspace only.
st.markdown('<div class="vp-footer"><span><strong>VICEPLUG HUB</strong> · RESEARCH → VERIFY → CREATE → REVIEW → PUBLISH</span><span>AI drafts require human fact-checking and rights review.</span></div>', unsafe_allow_html=True)
