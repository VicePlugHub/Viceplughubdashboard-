"""VicePlug Hub — GTA VI research and content operations dashboard.

Designed for Streamlit Community Cloud. Connects to Google Sheets and Groq
when credentials are supplied in Streamlit Secrets.
"""

import json
import os
from contextlib import contextmanager
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
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    px = None
    PLOTLY_AVAILABLE = False

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

/* Refined 2.0: balanced sizing, tighter cards, dedicated analytics spacing */
.block-container { max-width: 1780px; padding: 1.35rem clamp(.9rem, 1.8vw, 2rem) 3rem; }
.vp-page-head { margin-bottom: 1.55rem; padding-bottom: 1.25rem; }
.vp-page-head p { max-width: 920px; }
.vp-panel { padding: clamp(17px, 1.45vw, 23px); margin-bottom: 17px; }
.vp-card { padding: 18px 19px; min-height: 124px; border-radius: 16px; }
.vp-card-grid-note { margin: 0 0 13px; font-size: .78rem; }
.vp-result-row { border:1px solid rgba(153,173,211,.16); border-radius:16px; padding:17px 18px 15px; background:linear-gradient(130deg,rgba(20,30,52,.98),rgba(10,16,30,.98)); margin:0 0 3px; box-shadow:0 10px 25px rgba(0,0,0,.10); overflow-wrap:anywhere; transition:border-color .18s ease,transform .18s ease; }
.vp-result-row:hover { border-color:rgba(183,123,255,.4); transform:translateY(-1px); }
.vp-result-eyebrow { color:#a995df; font-size:.61rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:6px; }
.vp-result-title { color:#fbfcff; font:700 clamp(.96rem,1.02vw,1.1rem)/1.38 'Space Grotesk',sans-serif; letter-spacing:-.02em; margin:0 0 7px; }
.vp-result-summary { color:#aab8d0; font-size:.82rem; line-height:1.58; margin:0 0 10px; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.vp-result-meta { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.vp-result-chip { display:inline-flex; align-items:center; padding:5px 8px; border:1px solid rgba(151,169,202,.14); background:rgba(7,11,23,.48); border-radius:8px; color:#c7d4e9; font-size:.65rem; font-weight:650; }
.vp-result-chip.status { color:#dccbff; background:rgba(130,83,223,.1); border-color:rgba(167,139,250,.22); }
.vp-result-chip.fact { color:#ffdda5; background:rgba(244,195,106,.07); border-color:rgba(244,195,106,.2); }
.vp-result-date { color:#7787a4; font-size:.68rem; margin-top:8px; }
.vp-setting-status { min-height:112px; padding:17px 17px 15px; border:1px solid rgba(153,173,211,.15); border-radius:16px; background:linear-gradient(145deg,rgba(18,28,48,.95),rgba(10,16,30,.95)); box-shadow:0 10px 24px rgba(0,0,0,.08); }
.vp-setting-status-label { color:#8e9db7; font-size:.68rem; text-transform:uppercase; font-weight:800; letter-spacing:.12em; margin-bottom:10px; }
.vp-setting-status-value { font:700 1rem/1.35 'Space Grotesk',sans-serif; color:#f5f7ff; margin-bottom:7px; overflow-wrap:anywhere; }
.vp-setting-status-note { color:#8796b0; font-size:.76rem; line-height:1.55; }
.vp-setting-value { padding:15px 16px; border:1px solid rgba(153,173,211,.14); border-radius:14px; background:rgba(12,19,35,.72); margin-bottom:10px; min-height:82px; }
.vp-setting-value-label { color:#8292ae; font-size:.67rem; letter-spacing:.1em; text-transform:uppercase; font-weight:800; margin-bottom:7px; }
.vp-setting-value-data { color:#e9edfa; font-size:.91rem; font-weight:700; overflow-wrap:anywhere; line-height:1.5; }
.vp-settings-section { margin: 26px 0 13px; padding-top: 18px; border-top:1px solid rgba(153,173,211,.13); }
.vp-settings-section h2 { font-size:1.1rem; margin:0 0 6px; color:#f7f8ff; }
.vp-settings-section p { font-size:.82rem; line-height:1.65; color:#8999b3; margin:0; }
.vp-analytics-section-intro { margin:35px 0 19px; padding:17px 21px; border-left:3px solid #c084fc; border-radius:0 14px 14px 0; background:linear-gradient(90deg,rgba(167,139,250,.10),rgba(85,223,242,.025),transparent); }
.vp-analytics-section-intro .eyebrow { color:#c7a6ff; font-size:.65rem; letter-spacing:.16em; font-weight:800; }
.vp-analytics-section-intro h2 { font:700 1.25rem/1.3 'Space Grotesk',sans-serif; margin:6px 0 4px; color:#f7f8ff; }
.vp-analytics-section-intro p { color:#8e9db7; font-size:.82rem; line-height:1.6; margin:0; }
.vp-record-action-col { display:flex; flex-direction:column; justify-content:center; height:100%; }
.vp-record-action-col .stButton button { width:100%; white-space:normal; min-height:3.15rem; }
.vp-detail-hero { border:1px solid rgba(183,123,255,.28); border-radius:24px; padding:clamp(22px,3vw,36px); margin:.25rem 0 24px; background:radial-gradient(ellipse at 87% 4%,rgba(255,79,160,.15),transparent 32%),linear-gradient(142deg,#121b31,#101326 65%,#20162f); box-shadow:0 20px 55px rgba(0,0,0,.17); }
.vp-detail-title { font:700 clamp(1.5rem,2.5vw,2.2rem)/1.25 'Space Grotesk',sans-serif; color:#fff; letter-spacing:-.04em; margin:.55rem 0 1rem; overflow-wrap:anywhere; }
.vp-detail-url { overflow-wrap:anywhere; color:#7ce8f7; font-size:.88rem; line-height:1.7; }
.vp-detail-field { border:1px solid rgba(153,173,211,.14); border-radius:15px; padding:17px 18px; min-height:95px; margin-bottom:12px; background:linear-gradient(150deg,rgba(17,27,47,.88),rgba(10,16,30,.88)); overflow-wrap:anywhere; }
.vp-detail-field-label { color:#a995df; font-size:.66rem; text-transform:uppercase; letter-spacing:.13em; font-weight:800; margin-bottom:9px; }
.vp-detail-field-value { color:#e2e9f5; font-size:.88rem; line-height:1.75; white-space:pre-wrap; word-break:break-word; }
.vp-delete-zone { border:1px solid rgba(248,113,113,.26); background:rgba(127,29,29,.08); padding:20px; border-radius:17px; margin-top:22px; }
.vp-analytics-hero { border:1px solid rgba(183,123,255,.28); border-radius:24px; padding:27px 30px; margin-bottom:24px; background:radial-gradient(ellipse at 85% 0%,rgba(255,79,160,.16),transparent 32%),radial-gradient(ellipse at 4% 100%,rgba(85,223,242,.08),transparent 35%),linear-gradient(140deg,#131c32,#0c1222); }
.vp-analytics-hero h2 { color:#fff; font:700 clamp(1.35rem,2vw,1.8rem)/1.3 'Space Grotesk',sans-serif; letter-spacing:-.035em; margin:.35rem 0 .5rem; }
.vp-analytics-hero p { color:#aebbd1; line-height:1.75; margin:0; max-width:840px; font-size:.91rem; }
.vp-chart-panel { padding:20px 22px 16px; background:linear-gradient(150deg,rgba(15,23,41,.95),rgba(9,14,27,.98)); border:1px solid rgba(153,173,211,.14); border-radius:20px; margin-bottom:18px; }
.vp-chart-title { color:#f7f8ff; font:700 1rem 'Space Grotesk',sans-serif; margin-bottom:4px; }
.vp-chart-subtitle { color:#8494b0; font-size:.78rem; line-height:1.6; margin-bottom:14px; }
[data-testid="stPlotlyChart"] { border-radius:14px; overflow:hidden; }
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] { margin-bottom:16px; border-color:rgba(153,173,211,.16) !important; border-radius:20px !important; background:linear-gradient(150deg,rgba(15,23,41,.95),rgba(9,14,27,.98)); padding:14px !important; }
[data-testid="stExpander"] { margin:12px 0 18px; }
[data-testid="stHorizontalBlock"] { gap: clamp(12px, 1.4vw, 24px); }
.stMarkdown p { line-height:1.72; }
.stCaptionContainer { line-height:1.6; }
@media (max-width: 1050px) {
  .block-container { padding:1rem .9rem 2.4rem; }
  .vp-result-row { padding:15px; }
  .vp-analytics-hero { padding:22px; }
  .vp-setting-status { min-height:100px; }
}
@media (max-width: 650px) {
  .block-container { padding:.65rem .5rem 1.6rem; }
  .vp-page-head { margin-bottom:1.2rem; padding-bottom:1rem; }
  .vp-panel { padding:15px; margin-bottom:13px; }
  .vp-card { padding:15px; min-height:112px; }
  .vp-result-row { padding:14px; border-radius:14px; }
  .vp-result-chip { font-size:.62rem; }
  .vp-detail-hero { padding:19px; border-radius:18px; }
  .vp-detail-field { padding:14px; }
  .vp-analytics-hero { padding:18px; border-radius:18px; }
  .vp-chart-panel { padding:14px; border-radius:16px; }
  .vp-analytics-section-intro { margin-top:27px; padding:14px 15px; }
  .vp-setting-status { min-height:0; padding:15px; }
  .vp-setting-value { min-height:0; }
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
    worksheet_name: Optional[str] = None,
) -> None:
    """Render roomy editorial result rows that open a dedicated record detail view."""
    if records is None or records.empty:
        show_missing_data("No records match these filters.")
        return

    view = records.copy().drop(columns=["_numeric_score"], errors="ignore")
    page_size = max(1, min(int(max_items), 10))
    total_pages = max(1, (len(view) + page_size - 1) // page_size)
    page_key = f"{key_prefix}_page_index"
    current_page = int(st.session_state.get(page_key, 0) or 0)
    if current_page >= total_pages or current_page < 0:
        current_page = 0
        st.session_state[page_key] = 0
    start_at = current_page * page_size
    end_at = min(len(view), start_at + page_size)
    shown = view.iloc[start_at:end_at]
    st.markdown(
        f'<div class="vp-card-grid-note">Showing <b>{start_at + 1 if len(view) else 0}–{end_at}</b> of <b>{len(view)}</b> records · Open a record for full details and safe deletion.</div>',
        unsafe_allow_html=True,
    )
    if total_pages > 1:
        page_prev, page_info, page_next = st.columns([1, 2, 1], gap="medium")
        with page_prev:
            if st.button("← Previous", key=f"{key_prefix}_prev_page", disabled=current_page <= 0, use_container_width=True):
                st.session_state[page_key] = current_page - 1
                st.rerun()
        with page_info:
            st.markdown(f'<div style="text-align:center;padding:10px 4px;color:#98a9c2;font-size:.8rem">Page <b style="color:#f5f7ff">{current_page + 1}</b> of {total_pages}</div>', unsafe_allow_html=True)
        with page_next:
            if st.button("Next →", key=f"{key_prefix}_next_page", disabled=current_page >= total_pages - 1, use_container_width=True):
                st.session_state[page_key] = current_page + 1
                st.rerun()
    title_col = title_column(shown)
    source_col = first_matching_column(shown, ["Source", "Publisher", "Channel", "Source Domain", "Creator", "Website"])
    summary_col = first_matching_column(shown, [
        "AI Summary", "Summary", "AI Why It Matters", "Why It Matters", "Discovery Priority Reasons",
        "Description", "Moment Explanation", "Notes", "Research Type", "Commentary Draft"
    ])
    src_url_col = url_column(shown)
    score_col = score_column(shown)
    status_col_local = status_column(shown)
    fact_col_local = fact_column(shown)
    date_col = first_matching_column(shown, ["Published At", "Publication Date", "Date Published", "Indexed At", "Collected At (UTC)", "Date", "Timestamp", "End Timestamp"])

    target_sheet = worksheet_name or str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))
    visible_columns = max(1, min(int(columns_count or 1), 3))
    card_columns = st.columns(visible_columns, gap="medium") if visible_columns > 1 else [st.container()]
    for card_idx, (record_index, row) in enumerate(shown.iterrows()):
        with card_columns[card_idx % visible_columns]:
            title_raw = _value_text(row.get(title_col, ""), "Untitled research record") if title_col else "Untitled research record"
            summary_raw = _value_text(row.get(summary_col, ""), "No summary saved yet. Open the source and review the record details.") if summary_col else "No summary saved yet. Open the source and review the record details."
            source_raw = _value_text(row.get(source_col, ""), "") if source_col else ""
            source_url = _value_text(row.get(src_url_col, ""), "") if src_url_col else ""
            domain = ""
            if source_url.startswith(("https://", "http://")):
                try:
                    domain = urlparse(source_url).netloc.lower().removeprefix("www.")
                except Exception:
                    domain = ""
            source_label = source_raw or domain or "Source not recorded"
            score_num = number_value(row.get(score_col)) if score_col else None
            score_text = f"{score_num:.0f}/100" if score_num is not None else "Not scored"
            status_text = _value_text(row.get(status_col_local, ""), "Needs review") if status_col_local else "Needs review"
            fact_text = _value_text(row.get(fact_col_local, ""), "Unverified") if fact_col_local else "Unverified"
            date_text = _value_text(row.get(date_col, ""), "Date not recorded") if date_col else "Date not recorded"
            sheet_row = row.get("_sheet_row", None)
            try:
                sheet_row_num = int(float(sheet_row)) if sheet_row is not None and str(sheet_row).strip() else None
            except (TypeError, ValueError):
                sheet_row_num = None

            score_chip = f'<span class="vp-result-chip">◈ Priority {html.escape(score_text)}</span>'
            status_chip = f'<span class="vp-result-chip status">{safe_text(status_text, 48)}</span>'
            fact_chip = f'<span class="vp-result-chip fact">{safe_text(fact_text, 48)}</span>'
            st.markdown(
                f"""<article class="vp-result-row">
                  <div class="vp-result-eyebrow">VICEPLUG INTELLIGENCE · RECORD {start_at + card_idx + 1:02d}</div>
                  <div class="vp-result-title">{safe_text(title_raw, 260)}</div>
                  <p class="vp-result-summary">{safe_text(summary_raw, 330)}</p>
                  <div class="vp-result-meta"><span class="vp-result-chip">◉ {safe_text(source_label, 85)}</span>{score_chip}{status_chip}{fact_chip}</div>
                  <div class="vp-result-date">◷ {safe_text(date_text, 64)}{f' · Sheet row {sheet_row_num}' if sheet_row_num else ''}</div>
                </article>""",
                unsafe_allow_html=True,
            )
            action_cols = st.columns([1.2, 1], gap="small")
            with action_cols[0]:
                if st.button("View details ↗", key=f"{key_prefix}_detail_{sheet_row_num or record_index}_{card_idx}", type="primary", use_container_width=True):
                    row_payload: Dict[str, str] = {}
                    for field, value in row.to_dict().items():
                        if field == "_numeric_score" or field == "_sheet_row":
                            continue
                        row_payload[str(field)] = _value_text(value, "")
                    st.session_state["record_detail"] = {
                        "worksheet_name": target_sheet,
                        "sheet_row": sheet_row_num,
                        "record": row_payload,
                        "title_column": title_col or "",
                        "title_value": title_raw,
                        "url_column": src_url_col or "",
                        "url_value": source_url,
                        "return_tab": st.session_state.active_tab,
                        "return_key": key_prefix,
                        "deletable": bool(sheet_row_num and worksheet_name),
                    }
                    st.rerun()
            with action_cols[1]:
                if source_url.startswith(("https://", "http://")):
                    st.markdown(f'<div style="padding:10px 0"><a style="color:#82e8f6;font-weight:700;font-size:.76rem;text-decoration:none" href="{html.escape(source_url, quote=True)}" target="_blank" rel="noopener noreferrer">Open source ↗</a></div>', unsafe_allow_html=True)

    if total_pages > 1:
        st.caption(f"Showing {len(shown)} records on this page. Use Previous / Next to browse the rest without cluttering the workspace.")
    if show_raw_expander:
        with st.expander("Advanced · inspect raw worksheet columns", expanded=False):
            st.dataframe(clean_display_df(records, 24), use_container_width=True, hide_index=True, height=340)


def delete_record_from_worksheet(detail: Dict[str, Any]) -> str:
    """Delete one Google Sheets row only after verifying row identity to reduce stale-row risk."""
    sheet_name = str(detail.get("worksheet_name") or "").strip()
    sheet_row = int(detail.get("sheet_row") or 0)
    if not sheet_name or sheet_row < 2:
        raise RuntimeError("This record does not have a valid worksheet row and cannot be deleted from Google Sheets.")
    book = open_spreadsheet()
    ws = book.worksheet(sheet_name)
    headers = [str(value).strip() for value in ws.row_values(1)]
    current = ws.row_values(sheet_row)
    if not current:
        raise RuntimeError("That worksheet row is empty. Refresh the record list before trying again.")

    def index_for(header_name: str, candidates: List[str]) -> Optional[int]:
        if header_name:
            for i, header in enumerate(headers):
                if header.strip().lower() == header_name.strip().lower():
                    return i
        lowered = [h.strip().lower() for h in headers]
        for candidate in candidates:
            if candidate.lower() in lowered:
                return lowered.index(candidate.lower())
        return None

    title_idx = index_for(str(detail.get("title_column", "")), ["title", "video title", "story title", "headline", "topic", "name"])
    url_idx = index_for(str(detail.get("url_column", "")), ["source url", "video url", "url", "link", "source link", "youtube url"])
    expected_title = str(detail.get("title_value") or "").strip()
    expected_url = str(detail.get("url_value") or "").strip().rstrip("/")
    actual_title = str(current[title_idx]).strip() if title_idx is not None and title_idx < len(current) else ""
    actual_url = str(current[url_idx]).strip().rstrip("/") if url_idx is not None and url_idx < len(current) else ""
    if expected_url and expected_url.lower() != actual_url.lower():
        raise RuntimeError("The source URL in that row has changed or is now blank since you opened it. Reopen the record list and try again; nothing was deleted.")
    if expected_title and title_idx is not None and expected_title.casefold() != actual_title.casefold():
        raise RuntimeError("The title in that row has changed since you opened it. Reopen the record list and try again; nothing was deleted.")
    ws.delete_rows(sheet_row)
    return f"Deleted row {sheet_row} from {book.title} → {sheet_name}."


def close_record_detail() -> None:
    detail = st.session_state.get("record_detail", {}) or {}
    worksheet_name = str(detail.get("worksheet_name") or "Worksheet")
    sheet_row = detail.get("sheet_row")
    st.session_state.pop(f"confirm_delete_{worksheet_name}_{sheet_row}", None)
    st.session_state.pop("record_detail", None)


def render_record_detail(detail: Dict[str, Any]) -> None:
    """Dedicated record workspace for full information, source, and safe deletion."""
    record = detail.get("record", {}) or {}
    title = str(detail.get("title_value") or "Untitled research record")
    worksheet_name = str(detail.get("worksheet_name") or "Worksheet")
    source_url = str(detail.get("url_value") or "").strip()
    st.button("← Back to results", key="record_detail_back", on_click=close_record_detail)
    st.markdown(
        f"""<section class="vp-detail-hero"><div class="vp-eyebrow">RECORD DETAIL · {safe_text(worksheet_name, 80)}</div>
        <div class="vp-detail-title">{safe_text(title, 350)}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px"><span class="vp-pill">Human review required</span><span class="vp-pill">Record ID · row {html.escape(str(detail.get('sheet_row') or 'not linked'))}</span></div>
        {f'<div class="vp-detail-url"><a href="{html.escape(source_url, quote=True)}" target="_blank" rel="noopener noreferrer">Open original source ↗</a><br>{html.escape(source_url)}</div>' if source_url.startswith(('https://','http://')) else '<div class="vp-muted">No original source URL is recorded for this item.</div>'}
        </section>""",
        unsafe_allow_html=True,
    )
    display_priority = [
        "AI Summary", "Summary", "Why It Matters", "AI Why It Matters", "Discovery Priority Reasons",
        "AI Hook", "AI Commentary Draft", "AI On-Screen Text", "AI Title", "AI Caption", "AI Hashtags",
        "AI Verification Needed", "AI Rights Note", "AI Recommended Action", "Notes", "Description", "Moment Explanation"
    ]
    preferred = []
    for candidate in display_priority:
        for key, value in record.items():
            if key.strip().lower() == candidate.lower() and value not in (None, "") and key not in preferred:
                preferred.append(key)
    hidden_keys = {str(detail.get("title_column", "")), str(detail.get("url_column", ""))}
    fields = [key for key in preferred if key not in hidden_keys]
    fields += [key for key, value in record.items() if key not in preferred and key not in hidden_keys and value not in (None, "")]
    if fields:
        st.markdown("### Record intelligence")
        for offset in range(0, len(fields), 2):
            pair = fields[offset:offset + 2]
            cols = st.columns(2, gap="large")
            for col, field in zip(cols, pair):
                with col:
                    value = str(record.get(field, ""))
                    if field == detail.get("url_column") or field == detail.get("title_column"):
                        continue
                    st.markdown(f'<div class="vp-detail-field"><div class="vp-detail-field-label">{safe_text(field.replace("_", " "), 100)}</div><div class="vp-detail-field-value">{safe_text(value, 4000)}</div></div>', unsafe_allow_html=True)
    if not fields:
        st.info("No additional fields were saved for this record.")

    st.markdown("### Record actions")
    if source_url.startswith(("https://", "http://")):
        st.link_button("Open source article", source_url, use_container_width=True)
    with st.expander("Delete this record", expanded=False):
        st.markdown('<div class="vp-delete-zone"><strong style="color:#fca5a5">Permanent deletion</strong><div style="color:#d5b6b6;line-height:1.7;margin-top:7px">This removes the selected row from the Google Sheets worksheet. It cannot be undone from VicePlug Hub. Export or back up the sheet first if you may need this record later.</div></div>', unsafe_allow_html=True)
        if not detail.get("deletable"):
            st.warning("This record is not linked to a writable worksheet row in this view, so deletion is unavailable here.")
        else:
            confirm = st.checkbox("I understand this permanently deletes this record from Google Sheets.", key=f"confirm_delete_{worksheet_name}_{detail.get('sheet_row')}")
            if st.button("Delete record permanently", type="primary", disabled=not confirm, key=f"delete_record_{worksheet_name}_{detail.get('sheet_row')}"):
                try:
                    with st.spinner("Verifying record and deleting its worksheet row…"):
                        message = delete_record_from_worksheet(detail)
                    st.session_state.pop("record_detail", None)
                    st.session_state.pop(f"confirm_delete_{worksheet_name}_{detail.get('sheet_row')}", None)
                    st.session_state["record_action_notice"] = message
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete the record: {exc}")

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



def _analytics_theme(title: str) -> str:
    """Transparent, keyword-based topic grouping; not semantic AI clustering."""
    text = (title or "").casefold()
    groups = [
        ("Trailer & gameplay", ("trailer", "gameplay", "footage", "mission", "demo", "leak gameplay")),
        ("Map & locations", ("map", "vice city", "location", "island", "city", "building", "interior")),
        ("Characters & story", ("character", "lucia", "jason", "story", "protagonist", "mission")),
        ("Release & editions", ("release", "launch", "delay", "date", "edition", "pre-order", "preorder", "price")),
        ("Technology & visuals", ("graphics", "engine", "physics", "ray tracing", "technology", "performance", "npc", "ai system")),
        ("Official updates", ("rockstar", "take-two", "take two", "official", "Newswire", "statement", "investor")),
        ("Business & hiring", ("hiring", "job listing", "jobs", "studio", "earnings", "revenue", "investor", "development")),
        ("Rumours & theories", ("rumour", "rumor", "leak", "theory", "speculation", "alleged", "unconfirmed")),
    ]
    for label, terms in groups:
        if any(term in text for term in terms):
            return label
    return "Other / broad coverage"


def _plotly_layout(fig: Any, height: int = 330) -> Any:
    """Apply the shared dark-cinematic visual language to a Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=16, t=24, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#c6d2e6", size=12),
        title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="#9cacbf")),
        xaxis=dict(showgrid=False, zeroline=False, linecolor="rgba(151,169,202,.18)", tickfont=dict(color="#9aaac3")),
        yaxis=dict(showgrid=True, gridcolor="rgba(151,169,202,.10)", zeroline=False, linecolor="rgba(151,169,202,.12)", tickfont=dict(color="#9aaac3")),
        hoverlabel=dict(bgcolor="#111a2d", bordercolor="#8b5cf6", font=dict(color="#f5f7ff")),
    )
    return fig


@contextmanager
def chart_panel(title: str, subtitle: str):
    """Use a native Streamlit container so chart cards wrap widgets, not just HTML text."""
    with st.container(border=True):
        st.markdown(f'<div class="vp-chart-title">{html.escape(title)}</div><div class="vp-chart-subtitle">{html.escape(subtitle)}</div>', unsafe_allow_html=True)
        yield


def _to_utc_series(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, utc=True, errors="coerce", format="mixed")
    except (TypeError, ValueError):
        return pd.to_datetime(series, utc=True, errors="coerce")

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

def _discovery_signature(item: Dict[str, Any]) -> str:
    url = str(item.get("Source URL", "") or "").strip().rstrip("/").lower()
    return url or str(item.get("Title", "")).strip().casefold()


def _dismiss_discovery_result(position: int) -> None:
    """Dismiss one unsaved discovery result while preserving other selections."""
    old_results = list(st.session_state.get("news_discovery_results", []))
    if not (0 <= position < len(old_results)):
        return
    selected = {
        _discovery_signature(item)
        for index, item in enumerate(old_results)
        if st.session_state.get(f"news_discovery_pick_{index}", False)
        and index != position
    }
    old_count = len(old_results)
    old_results.pop(position)
    for index in range(old_count):
        st.session_state.pop(f"news_discovery_pick_{index}", None)
    st.session_state.news_discovery_results = old_results
    for index, item in enumerate(old_results):
        if _discovery_signature(item) in selected:
            st.session_state[f"news_discovery_pick_{index}"] = True


# -----------------------------------------------------------------------------
# Load records and build the shared application shell
# -----------------------------------------------------------------------------
df, worksheet, sheet_message, sheet_status = load_sheet_records()
PRIMARY_WORKSHEET_NAME = worksheet.title if worksheet is not None else str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))

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
            close_record_detail()
            st.session_state.active_tab = label
            st.rerun()
    st.markdown('<div class="vp-nav-foot">GOOD CONTENT<br><b style="color:#b8c4da">BUILDS BIGGER WORLDS.</b><br><span style="color:#586780">RESEARCH → VERIFY → CREATE</span></div>', unsafe_allow_html=True)

with col_main:
    if st.session_state.get("record_action_notice"):
        st.success(st.session_state.pop("record_action_notice"))
    if st.session_state.get("record_detail"):
        render_record_detail(st.session_state["record_detail"])
    # =====================================================================
    # DASHBOARD
    # =====================================================================
    elif st.session_state.active_tab == "Dashboard":
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
                render_record_cards(best, key_prefix="dashboard_top_opportunities", max_items=5, columns_count=1, worksheet_name=PRIMARY_WORKSHEET_NAME)
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
                    st.session_state.news_discovery_page_index = 0
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
            st.caption("Open a story for details, dismiss results you do not want, or select only the items worth saving. Duplicate links and titles already in Research Feed will be skipped.")
            discovery_page_size = 8
            discovery_total_pages = max(1, (len(found) + discovery_page_size - 1) // discovery_page_size)
            discovery_page_key = "news_discovery_page_index"
            discovery_page = int(st.session_state.get(discovery_page_key, 0) or 0)
            if discovery_page >= discovery_total_pages or discovery_page < 0:
                discovery_page = 0
                st.session_state[discovery_page_key] = 0
            discovery_start = discovery_page * discovery_page_size
            visible_found = [(i, found[i]) for i in range(discovery_start, min(len(found), discovery_start + discovery_page_size))]
            if discovery_total_pages > 1:
                prev_discovery, discovery_info, next_discovery = st.columns([1, 2, 1], gap="medium")
                with prev_discovery:
                    if st.button("← Previous results", key="news_discovery_prev", disabled=discovery_page <= 0, use_container_width=True):
                        st.session_state[discovery_page_key] = discovery_page - 1
                        st.rerun()
                with discovery_info:
                    st.markdown(f'<div style="text-align:center;padding:10px 4px;color:#98a9c2;font-size:.8rem">Page <b style="color:#f5f7ff">{discovery_page + 1}</b> of {discovery_total_pages} · {len(found)} results</div>', unsafe_allow_html=True)
                with next_discovery:
                    if st.button("Next results →", key="news_discovery_next", disabled=discovery_page >= discovery_total_pages - 1, use_container_width=True):
                        st.session_state[discovery_page_key] = discovery_page + 1
                        st.rerun()
            selected_positions = {i for i in range(len(found)) if st.session_state.get(f"news_discovery_pick_{i}", False)}
            for offset in range(0, len(visible_found), 2):
                slots = st.columns(2, gap="large")
                for local_i, (position, item) in enumerate(visible_found[offset:offset + 2]):
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
                        action_view, action_dismiss, action_select = st.columns([1.15, 1.0, 1.65], gap="small")
                        with action_view:
                            if st.button("View details ↗", key=f"news_discovery_detail_{position}", use_container_width=True):
                                item_title = str(item.get("Title", "Untitled story"))
                                item_url = str(item.get("Source URL", "") or "")
                                st.session_state["record_detail"] = {
                                    "worksheet_name": "Unsaved discovery result",
                                    "sheet_row": None,
                                    "record": {str(k): str(v or "") for k, v in item.items()},
                                    "title_column": "Title",
                                    "title_value": item_title,
                                    "url_column": "Source URL",
                                    "url_value": item_url,
                                    "return_tab": st.session_state.active_tab,
                                    "return_key": "news_discovery_results",
                                    "deletable": False,
                                }
                                st.rerun()
                        with action_dismiss:
                            st.button("Dismiss", key=f"news_discovery_dismiss_{position}", on_click=_dismiss_discovery_result, args=(position,), use_container_width=True, help="Remove this item from the current search results. It does not delete a saved spreadsheet row.")
                        with action_select:
                            checked = st.checkbox("Select to save", key=f"news_discovery_pick_{position}")
                            if checked:
                                selected_positions.add(position)
                            else:
                                selected_positions.discard(position)
            save_col, clear_col = st.columns([2, 1], gap="large")
            with save_col:
                if st.button(f"💾 Save {len(selected_positions)} selected stories to Google Sheets", type="primary", use_container_width=True, disabled=not selected_positions):
                    try:
                        selected_articles = [found[i] for i in sorted(selected_positions)]
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
                    st.session_state.news_discovery_page_index = 0
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
            render_record_cards(saved_view, key_prefix="saved_news_cards", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=NEWS_WORKSHEET_NAME)
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
            render_record_cards(view, key_prefix="video_discovery_cards", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=PRIMARY_WORKSHEET_NAME)

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
            render_record_cards(opp_df, key_prefix="opportunities_unscored", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=NEWS_WORKSHEET_NAME if opportunity_source == "Research Feed" else PRIMARY_WORKSHEET_NAME)
        else:
            opp_score_col = score_column(opp_df)
            min_score = st.slider("Minimum priority score", 0, 100, 45, key=f"minimum_priority_{opportunity_source}")
            ranked = sorted_by_score(opp_df)
            ranked = ranked[ranked["_numeric_score"].fillna(-1) >= min_score]
            st.caption(f"Showing {len(ranked)} records scoring {min_score}+ from {opportunity_source}. Scores use metadata heuristics or saved AI analysis, depending on the selected field.")
            render_record_cards(ranked.drop(columns=["_numeric_score"], errors="ignore"), key_prefix=f"opportunities_{opportunity_source}", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=NEWS_WORKSHEET_NAME if opportunity_source == "Research Feed" else PRIMARY_WORKSHEET_NAME)
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
                render_record_cards(pipeline_df, key_prefix=f"pipeline_no_status_{pipeline_source}", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=pipeline_sheet_name)
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
                render_record_cards(shown, key_prefix=f"pipeline_{st.session_state.active_tab}_{pipeline_source}", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=pipeline_sheet_name)
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
        render_page_header("Trends & Analytics", "A visual intelligence layer for topic momentum, source mix, priority, and workflow health—only from collected records.")
        st.markdown('<section class="vp-analytics-hero"><div class="vp-eyebrow">SIGNAL DESK / LIVE SHEET DATA</div><h2>Find the story behind the headlines.</h2><p>Explore which GTA VI topics appear most often, how recent your coverage is, where your sources come from, and what still needs review. Topic groups are keyword-based research signals, not proof of audience demand or semantic AI clustering.</p></section>', unsafe_allow_html=True)

        analysis_source = st.radio("Analyze dataset", ["Combined research", "Video Discovery", "Research Feed"], horizontal=True, key="analytics_dataset")
        if analysis_source == "Research Feed":
            analytics_df, _, analytics_message, analytics_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
            analytics_label = "Research Feed"
        elif analysis_source == "Video Discovery":
            analytics_df, analytics_label, analytics_message, analytics_status = df, PRIMARY_WORKSHEET_NAME, sheet_message, sheet_status
        else:
            news_analytics_df, _, news_analytics_message, news_analytics_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
            video_analytics_df = df.copy() if df is not None else pd.DataFrame()
            chunks = []
            for source_name, source_df in [(PRIMARY_WORKSHEET_NAME, video_analytics_df), (NEWS_WORKSHEET_NAME, news_analytics_df)]:
                if source_df is not None and not source_df.empty:
                    part = source_df.copy()
                    part["_analytics_source"] = source_name
                    chunks.append(part)
            analytics_df = pd.concat(chunks, ignore_index=True, sort=False) if chunks else pd.DataFrame()
            analytics_label = "Combined research"
            analytics_message = "Combined the available Video Discovery and Research Feed worksheets."
            analytics_status = "connected" if chunks else "empty"

        if analytics_df.empty:
            show_missing_data(analytics_message if analytics_status != "connected" else "No records are available for trend analysis yet.")
        else:
            title_col = title_column(analytics_df)
            date_candidates = ["Collected At (UTC)", "Indexed At", "Published At", "Publication Date", "Date Published", "End Timestamp", "Created At", "Timestamp", "Date"]
            score_candidates = ["AI Priority Score", "Discovery Priority Score", "Priority Score", "Viral Score", "Priority", "Score"]
            status_candidates = ["Review Status", "Pipeline Status", "Content Status", "Status"]
            source_candidates = ["Source", "Publisher", "Source Domain", "Channel", "Website", "Creator"]
            views_col = first_matching_column(analytics_df, ["Views", "View Count", "Views Count", "Video Views"])

            period_col, source_col_ui = st.columns([1.1, 1.2], gap="large")
            with period_col:
                analytics_period = st.selectbox("Time window", ["Past 7 days", "Past 30 days", "Past 90 days", "All records with dates"], index=1, key="analytics_period")
            with source_col_ui:
                if "_analytics_source" in analytics_df.columns:
                    source_options = ["All sources"] + sorted([str(x) for x in analytics_df["_analytics_source"].dropna().unique() if str(x).strip()])
                    source_filter = st.selectbox("Worksheet", source_options, key="analytics_worksheet_filter")
                    if source_filter != "All sources":
                        analytics_df = analytics_df[analytics_df["_analytics_source"].astype(str) == source_filter].copy()
                else:
                    st.markdown('<div class="vp-muted" style="padding:12px 0">Source: ' + safe_text(analytics_label, 60) + '</div>', unsafe_allow_html=True)

            enriched = analytics_df.copy()
            if title_col:
                enriched["_analytics_title"] = enriched[title_col].fillna("").astype(str)
            else:
                enriched["_analytics_title"] = "Untitled record"
            score_columns = []
            for candidate in score_candidates:
                found_col = first_matching_column(analytics_df, [candidate])
                if found_col and found_col not in score_columns:
                    score_columns.append(found_col)
            if score_columns:
                numeric_scores = pd.concat([enriched[col].apply(number_value).rename(str(i)) for i, col in enumerate(score_columns)], axis=1)
                enriched["_analytics_score"] = numeric_scores.bfill(axis=1).iloc[:, 0]
            else:
                enriched["_analytics_score"] = pd.Series([None] * len(enriched), index=enriched.index, dtype="object")

            def _coalesced_text(candidates: list, default: str) -> pd.Series:
                columns = []
                for candidate in candidates:
                    found_col = first_matching_column(analytics_df, [candidate])
                    if found_col and found_col not in columns:
                        columns.append(found_col)
                if not columns:
                    return pd.Series([default] * len(enriched), index=enriched.index, dtype="object")
                values = pd.concat([enriched[col].fillna("").astype(str).str.strip().replace("", pd.NA).rename(str(i)) for i, col in enumerate(columns)], axis=1)
                return values.bfill(axis=1).iloc[:, 0].fillna(default)

            enriched["_analytics_status"] = _coalesced_text(status_candidates, "Unspecified")
            enriched["_analytics_source_label"] = _coalesced_text(source_candidates, "Source not recorded")
            parsed_dates = []
            for candidate in date_candidates:
                found_col = first_matching_column(analytics_df, [candidate])
                if found_col and found_col not in parsed_dates:
                    parsed_dates.append(found_col)
            if parsed_dates:
                parsed_date_frame = pd.concat([_to_utc_series(enriched[col]).rename(str(i)) for i, col in enumerate(parsed_dates)], axis=1)
                enriched["_analytics_date"] = parsed_date_frame.bfill(axis=1).iloc[:, 0]
            else:
                enriched["_analytics_date"] = pd.Series(pd.NaT, index=enriched.index, dtype="datetime64[ns, UTC]")
            enriched["_analytics_theme"] = enriched["_analytics_title"].map(_analytics_theme)
            now_utc = pd.Timestamp.now(tz="UTC")
            has_any_dates = int(enriched["_analytics_date"].notna().sum()) > 0
            if not has_any_dates:
                filtered = enriched.copy()
            elif analytics_period != "All records with dates":
                days = {"Past 7 days": 7, "Past 30 days": 30, "Past 90 days": 90}[analytics_period]
                cutoff = now_utc - pd.Timedelta(days=days)
                dated = enriched[enriched["_analytics_date"].notna()].copy()
                filtered = dated[dated["_analytics_date"] >= cutoff].copy()
            else:
                filtered = enriched[enriched["_analytics_date"].notna()].copy()

            recent_count = int((filtered["_analytics_date"] >= now_utc - pd.Timedelta(hours=24)).sum()) if len(filtered) else 0
            scored = filtered[filtered["_analytics_score"].notna()].copy()
            pending = int(filtered["_analytics_status"].str.lower().str.contains("review|pending|needs|unreviewed|draft", regex=True).sum())
            high_priority = int((filtered["_analytics_score"] >= 75).sum()) if len(scored) else 0
            avg_score = f"{scored['_analytics_score'].mean():.0f}" if len(scored) else "—"
            metric_cols = st.columns(4, gap="large")
            with metric_cols[0]: metric_card("Records in window", f"{len(filtered):,}", "Records shown for selected period", "◷", "#38d9f5")
            with metric_cols[1]: metric_card("Added / indexed in 24h", f"{recent_count:,}", "Based on recorded timestamps", "✦", "#ff4fa0")
            with metric_cols[2]: metric_card("High-priority leads", f"{high_priority:,}", "Score ≥ 75; sorting aid only", "🎯", "#a78bfa")
            with metric_cols[3]: metric_card("Needs attention", f"{pending:,}", f"Average score: {avg_score}/100" if avg_score != "—" else "Status and score fields", "◎", "#f4c36a")

            if not has_any_dates:
                st.warning("No usable timestamps were detected. Add consistent publication, indexing, or collection dates to unlock the timeline. Topic and source charts still use the available records.")
            elif filtered.empty:
                st.info(f"No records with parseable dates fall inside {analytics_period.lower()}. Choose a longer period or use All records with dates.")

            # Clear visual break between the KPI row and the first chart row.
            st.markdown(
                '<div class="vp-analytics-section-intro"><div class="eyebrow">SIGNAL INTELLIGENCE</div>'
                '<h2>Research momentum &amp; priority profile</h2>'
                '<p>Explore when records arrive and how saved priority scores are distributed. A little extra separation keeps this analysis distinct from the summary metrics above.</p></div>',
                unsafe_allow_html=True,
            )

            # Timeline chart: records per day, using actual stored dates only.
            c_timeline, c_distribution = st.columns([1.65, 1], gap="large")
            with c_timeline:
                with chart_panel('Research momentum', 'Records collected or indexed per day within the selected window.'):
                    timeline_rows = filtered[filtered["_analytics_date"].notna()].copy()
                    if not timeline_rows.empty:
                        timeline_rows["Day"] = timeline_rows["_analytics_date"].dt.floor("D")
                        timeline = timeline_rows.groupby("Day").size().rename("Records").reset_index()
                        if PLOTLY_AVAILABLE:
                            fig = px.area(timeline, x="Day", y="Records", markers=True)
                            fig.update_traces(line=dict(color="#c084fc", width=3), fillcolor="rgba(192,132,252,.15)", marker=dict(size=7, color="#ff66ae"), hovertemplate="%{x|%b %d}<br>Records: %{y}<extra></extra>")
                            _plotly_layout(fig, 340)
                            fig.update_xaxes(tickformat="%b %d")
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                        else:
                            st.line_chart(timeline.set_index("Day")["Records"], color="#c084fc")
                    else:
                        st.markdown('<div class="vp-empty">Timeline data will appear when records contain parseable dates.</div>', unsafe_allow_html=True)
            with c_distribution:
                with chart_panel('Priority profile', 'Distribution of scores stored in the selected dataset.'):
                    if len(scored):
                        bins = pd.cut(scored["_analytics_score"], bins=[0, 20, 40, 60, 75, 90, 100], include_lowest=True, right=True)
                        dist = bins.value_counts(sort=False).reset_index()
                        dist.columns = ["Score band", "Records"]
                        dist["Score band"] = dist["Score band"].astype(str)
                        if PLOTLY_AVAILABLE:
                            fig = px.bar(dist, x="Score band", y="Records")
                            fig.update_traces(marker_color="#ff5ca8", marker_line_color="rgba(255,255,255,.12)", marker_line_width=1, hovertemplate="%{x}<br>Records: %{y}<extra></extra>")
                            _plotly_layout(fig, 340)
                            fig.update_xaxes(title=None, tickangle=-22)
                            fig.update_yaxes(title=None, dtick=1 if dist["Records"].max() <= 10 else None)
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                        else:
                            st.bar_chart(dist.set_index("Score band")["Records"], color="#ff5ca8")
                    else:
                        st.markdown('<div class="vp-empty">No numeric priority scores are available for this selection.</div>', unsafe_allow_html=True)

            c_topics, c_sources = st.columns(2, gap="large")
            with c_topics:
                with chart_panel('Topic signals', 'Keyword-based grouping of titles; not semantic AI clustering.'):
                    if len(filtered):
                        topic_counts = filtered["_analytics_theme"].value_counts().head(9).sort_values()
                        if PLOTLY_AVAILABLE and len(topic_counts):
                            fig = px.bar(x=topic_counts.values, y=topic_counts.index, orientation="h", labels={"x": "Records", "y": "Theme"})
                            fig.update_traces(marker_color="#48cde3", marker_line_width=0, hovertemplate="%{y}<br>Records: %{x}<extra></extra>")
                            _plotly_layout(fig, max(280, 38 * len(topic_counts) + 70))
                            fig.update_xaxes(title=None)
                            fig.update_yaxes(title=None, showgrid=False)
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                        elif len(topic_counts):
                            st.bar_chart(topic_counts, color="#48cde3")
                        else:
                            st.info("No titles were available for theme grouping.")
                    else:
                        st.info("No records fall within the selected time window.")
            with c_sources:
                with chart_panel('Source landscape', 'Most represented publishers or channels in the selected records.'):
                    source_counts = filtered["_analytics_source_label"].replace("", "Source not recorded").value_counts().head(8)
                    if PLOTLY_AVAILABLE and len(source_counts):
                        fig = px.pie(values=source_counts.values, names=source_counts.index, hole=.68)
                        fig.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="#0b1020", width=3)), hovertemplate="%{label}<br>%{value} records (%{percent})<extra></extra>")
                        _plotly_layout(fig, 320)
                        fig.update_layout(margin=dict(l=8, r=110, t=18, b=8), showlegend=True, legend=dict(orientation="v", x=1.01, y=.5, xanchor="left", yanchor="middle", font=dict(color="#aab8d0", size=9)))
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                    elif len(source_counts):
                        st.bar_chart(source_counts, color="#a78bfa")
                    else:
                        st.info("No source / publisher column was detected.")

            c_status, c_top = st.columns([1, 1.35], gap="large")
            with c_status:
                with chart_panel('Workflow health', 'Distribution of saved review statuses.'):
                    status_counts = filtered["_analytics_status"].replace("", "Unspecified").value_counts().head(9)
                    if PLOTLY_AVAILABLE and len(status_counts):
                        fig = px.pie(values=status_counts.values, names=status_counts.index, hole=.62)
                        fig.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="#0b1020", width=3)), hovertemplate="%{label}<br>%{value} records (%{percent})<extra></extra>")
                        _plotly_layout(fig, 315)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                    elif len(status_counts):
                        st.bar_chart(status_counts, color="#a78bfa")
                    else:
                        st.info("No workflow statuses are recorded.")
            with c_top:
                with chart_panel('Priority watchlist', 'Highest-scoring leads in the current selection, for manual review.'):
                    watch = filtered[filtered["_analytics_score"].notna()].sort_values("_analytics_score", ascending=False).head(6)
                    if len(watch):
                        for _, item in watch.iterrows():
                            st.markdown(f'<div class="vp-result-row" style="padding:14px 16px;margin-bottom:10px"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:15px"><div><div style="color:#f5f7ff;font-weight:700;line-height:1.5">{safe_text(item["_analytics_title"], 180)}</div><div style="font-size:.73rem;color:#8999b2;margin-top:5px">{safe_text(item["_analytics_theme"], 55)} · {safe_text(item["_analytics_source_label"], 70)}</div></div><span class="vp-record-score">{float(item["_analytics_score"]):.0f}/100</span></div></div>', unsafe_allow_html=True)
                    else:
                        st.info("No scored items are available for the watchlist.")

            if views_col:
                views = filtered[views_col].apply(number_value).dropna()
                with chart_panel('Recorded video views', 'Actual saved view counts only; no view data is estimated.'):
                    if len(views):
                        view_rows = filtered.loc[views.index, [title_col] if title_col else []].copy() if title_col else pd.DataFrame(index=views.index)
                        view_rows["Views"] = views
                        view_rows["Title"] = view_rows[title_col].astype(str) if title_col else view_rows.index.astype(str)
                        view_rows = view_rows.sort_values("Views", ascending=False).head(12).sort_values("Views")
                        if PLOTLY_AVAILABLE:
                            fig = px.bar(view_rows, x="Views", y="Title", orientation="h")
                            fig.update_traces(marker_color="#51d7e8", hovertemplate="%{y}<br>Views: %{x:,.0f}<extra></extra>")
                            _plotly_layout(fig, max(280, len(view_rows) * 31 + 60))
                            fig.update_xaxes(title=None, tickformat="~s")
                            fig.update_yaxes(title=None, showgrid=False)
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                        else:
                            st.bar_chart(view_rows.set_index("Title")["Views"], color="#51d7e8")
                    else:
                        st.info("The views column exists, but no numeric view counts are present in this period.")
            st.caption(f"Dataset: {analytics_label} · {len(enriched)} total records loaded · {len(filtered)} records included in the current analytics window. Date and score interpretations depend on the source worksheet's data quality.")

    # =====================================================================
    # GOOGLE SHEETS SYNC
    # =====================================================================
    elif st.session_state.active_tab == "Google Sheets Sync":
        render_page_header("Google Sheets Sync", "Inspect your connected research worksheet and check connection setup.")
        if sheet_status == "connected":
            st.success(sheet_message)
            st.caption("This screen reads your configured research worksheet. Status edits in Content Pipeline / Review Queue are written back when a supported status column exists.")
            render_record_cards(df, key_prefix="sheets_sync_cards", max_items=40, columns_count=2, show_raw_expander=True, worksheet_name=PRIMARY_WORKSHEET_NAME)
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
        render_page_header("Settings & Integrations", "A clear view of service health, active worksheet names and required configuration.", eyebrow="SYSTEM CONTROL")
        groq_key_present = bool(get_secret("GROQ_API_KEY"))
        groq_ok = groq_key_present and HAS_GROQ
        service_account_present = bool(get_service_account_info() or (get_secret("GOOGLE_SERVICE_ACCOUNT_FILE") and os.path.exists(str(get_secret("GOOGLE_SERVICE_ACCOUNT_FILE")))))

        st.markdown(
            '<div class="vp-settings-section" style="margin-top:0;padding-top:0;border-top:0"><h2>Connection health</h2>'
            '<p>These indicators show whether configuration is present. API key presence alone does not guarantee every request will succeed.</p></div>',
            unsafe_allow_html=True,
        )
        status_cols = st.columns(3, gap="medium")
        status_items = [
            ("Groq API", "Key configured" if groq_ok else ("Package missing" if groq_key_present else "Not configured"), "Secret detected and Groq client available." if groq_ok else ("Install the groq package in requirements.txt." if groq_key_present else "Add GROQ_API_KEY to Streamlit Secrets."), "#4adea6" if groq_ok else "#f4c36a"),
            ("Google Sheets", "Connected" if sheet_status == "connected" else "Not connected", sheet_message if sheet_status == "connected" else "Check the spreadsheet ID, service-account credentials, and sharing permissions.", "#4adea6" if sheet_status == "connected" else "#f4c36a"),
            ("Service account", "Configured" if service_account_present else "Missing", "Credentials were detected by the app." if service_account_present else "Add the service-account details to Streamlit Secrets or configure the credential file.", "#4adea6" if service_account_present else "#f4c36a"),
        ]
        for col, (label, value, note, color) in zip(status_cols, status_items):
            with col:
                st.markdown(
                    f'<div class="vp-setting-status"><div class="vp-setting-status-label">{html.escape(label)}</div>'
                    f'<div class="vp-setting-status-value" style="color:{color}">{html.escape(value)}</div>'
                    f'<div class="vp-setting-status-note">{html.escape(str(note)[:220])}</div></div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="vp-settings-section"><h2>Workspace configuration</h2>'
            '<p>Values below are read from the current application configuration. Change them through Streamlit Secrets or the corresponding environment configuration—not by editing this display.</p></div>',
            unsafe_allow_html=True,
        )
        model_name = str(get_secret("GROQ_MODEL", "openai/gpt-oss-20b"))
        video_sheet_name = str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))
        news_sheet_name = str(get_secret("NEWS_RESEARCH_WORKSHEET", NEWS_WORKSHEET_NAME))
        config_cols = st.columns(2, gap="large")
        with config_cols[0]:
            st.markdown(
                '<div class="vp-setting-value"><div class="vp-setting-value-label">AI provider</div>'
                f'<div class="vp-setting-value-data">Groq</div><div class="vp-setting-status-note" style="margin-top:5px">Model: {html.escape(model_name)}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="vp-setting-value"><div class="vp-setting-value-label">Video research worksheet</div>'
                f'<div class="vp-setting-value-data">{html.escape(video_sheet_name)}</div><div class="vp-setting-status-note" style="margin-top:5px">Saved video research and AI analysis fields.</div></div>',
                unsafe_allow_html=True,
            )
        with config_cols[1]:
            st.markdown(
                '<div class="vp-setting-value"><div class="vp-setting-value-label">News research worksheet</div>'
                f'<div class="vp-setting-value-data">{html.escape(news_sheet_name)}</div><div class="vp-setting-status-note" style="margin-top:5px">Scheduled and on-demand discovery leads.</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="vp-setting-value"><div class="vp-setting-value-label">Background collector</div>'
                '<div class="vp-setting-value-data">GitHub Actions</div><div class="vp-setting-status-note" style="margin-top:5px">Scheduled collection runs outside this dashboard; check the repository Actions tab for run history.</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="vp-settings-section"><h2>Configuration guidance</h2>'
            '<p>Keep private keys in secret storage. This page never displays the live secret values.</p></div>',
            unsafe_allow_html=True,
        )
        if not groq_ok:
            st.warning("Groq AI analysis may be unavailable until GROQ_API_KEY is configured and the groq package is installed.")
        if sheet_status != "connected":
            st.warning("Google Sheets is not connected. Review GOOGLE_SHEET_ID, the service-account fields, and Editor access to the spreadsheet.")
        st.info("For scheduled research, manage GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON under GitHub repository Settings → Secrets and variables → Actions. These are separate from Streamlit Secrets.")
        with st.expander("Secret names and example format", expanded=False):
            st.markdown("Use your real values in Streamlit Secrets. The template below contains placeholders only; do not paste private credentials into chat or commit them to GitHub.")
            st.code('GROQ_API_KEY = "your-groq-api-key"\nGROQ_MODEL = "openai/gpt-oss-20b"\nGOOGLE_SHEET_ID = "your-google-sheet-id"\nVIDEO_DISCOVERY_WORKSHEET = "Video Discovery"\nNEWS_RESEARCH_WORKSHEET = "Research Feed"\n\n[gcp_service_account]\ntype = "service_account"\nproject_id = "..."\nprivate_key_id = "..."\nprivate_key = "..."\nclient_email = "..."\nclient_id = "..."\nauth_uri = "https://accounts.google.com/o/oauth2/auth"\ntoken_uri = "https://oauth2.googleapis.com/token"\nauth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"\nclient_x509_cert_url = "..."', language="toml")

# Footer in normal flow, inside the selected workspace only.
st.markdown('<div class="vp-footer"><span><strong>VICEPLUG HUB</strong> · RESEARCH → VERIFY → CREATE → REVIEW → PUBLISH</span><span>AI drafts require human fact-checking and rights review.</span></div>', unsafe_allow_html=True)
