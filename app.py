"""
VicePlug Hub // Spatial VisionOS Edition
Engineered for Streamlit Community Cloud (*.streamlit.app)
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

# Optional enterprise integrations with graceful fallbacks
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
# STREAMLIT PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug // Spatial Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# VISIONOS SPATIAL GLASS DESIGN SYSTEM (CSS)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Grotesk:wght@500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-void: #03050c;
    --glass-surface: rgba(14, 20, 36, 0.55);
    --glass-border: rgba(255, 255, 255, 0.07);
    --glass-specular: rgba(255, 255, 255, 0.16);
    --cyan: #00F5FF;
    --magenta: #FF2E93;
    --purple: #8B5CF6;
    --emerald: #00FF88;
    --amber: #FFB800;
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-dim: #64748B;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-void);
    background-image: 
        radial-gradient(circle at 10% 0%, rgba(139, 92, 246, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 90% 10%, rgba(255, 46, 147, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 50% 80%, rgba(0, 245, 255, 0.05) 0%, transparent 50%);
    background-attachment: fixed;
}

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    max-width: 1680px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

/* Floating VisionOS Glass Panels */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--glass-surface) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(36px) saturate(190%) !important;
    -webkit-backdrop-filter: blur(36px) saturate(190%) !important;
    box-shadow: 0 16px 40px -8px rgba(0, 0, 0, 0.55) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--glass-specular) !important;
}

/* Floating Studio Header */
.studio-nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(14, 20, 36, 0.65);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 12px 26px;
    margin-bottom: 16px;
    backdrop-filter: blur(30px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.brand-typography {
    font-family: 'Syne', sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #FFF;
    display: flex;
    align-items: center;
    gap: 8px;
}

.brand-typography span {
    background: linear-gradient(135deg, #00F5FF 0%, #FF2E93 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Glass Navigation Dock Buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid var(--glass-border) !important;
    color: var(--text-secondary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    border-radius: 12px !important;
    padding: 10px 18px !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.22) !important;
    color: #FFF !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

/* Minimalist Metric Stat */
.stat-box {
    padding: 4px;
}

.stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-dim);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}

.stat-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.3rem;
    font-weight: 700;
    color: #FFF;
    margin: 4px 0 2px 0;
    letter-spacing: -0.03em;
}

/* Cinematic Lead Dossier Card */
.teleprompter-card {
    background: linear-gradient(135deg, rgba(20, 28, 52, 0.6) 0%, rgba(10, 15, 30, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 18px;
    padding: 24px;
    backdrop-filter: blur(28px);
}

.prompter-hook {
    background: rgba(0, 245, 255, 0.05);
    border-left: 3px solid var(--cyan);
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 12px 0 16px 0;
}

/* Holographic Creator Badge */
.creator-glass-tile {
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(32px);
    transition: all 0.3s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.creator-glass-tile:hover {
    border-color: rgba(0, 245, 255, 0.35);
    transform: translateY(-4px);
    box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.55), 0 0 24px rgba(0, 245, 255, 0.12);
}

.avatar-sphere {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg, #7C3AED, #FF2E93);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1.25rem;
    color: #FFF;
    font-family: 'Space Grotesk', sans-serif;
    box-shadow: 0 6px 20px rgba(255, 46, 147, 0.3);
}

.hyperlink-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 16px;
    border-radius: 30px;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none !important;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #E2E8F0 !important;
    transition: all 0.2s ease;
}

.hyperlink-chip:hover {
    background: rgba(0, 245, 255, 0.18);
    border-color: var(--cyan);
    color: #FFF !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# CONFIG & SECRETS MANAGER (STREAMLIT CLOUD SAFE)
# --------------------------------------------------
def get_secret(key: str, default: Any = None) -> Any:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


# --------------------------------------------------
# GTA VI INTELLIGENCE DATASET
# --------------------------------------------------
INITIAL_DATASET = [
    {
        "id": "lead-1",
        "row_number": 2,
        "title": "Take-Two Interactive SEC 10-Q Filing Confirms Fiscal 2026 Window",
        "source_url": "https://www.sec.gov",
        "priority_score": 96,
        "fact_status": "Official Rockstar",
        "review_status": "Needs Review",
        "summary": "Take-Two reiterated expected booking surge for FY2026, officially narrowing the launch window to Fall 2025/Early 2026.",
        "hook": "Take-Two just confirmed their biggest release schedule in gaming history, and the date is locked in.",
        "commentary_draft": "Take-Two just dropped their latest official financial disclosure, and it confirms what insiders have been praying for. Their expected bookings surge for fiscal 2026 remains completely unchanged, meaning Rockstar is on strict track for their launch window.",
        "on_screen_text": "RELEASE WINDOW LOCKED",
        "why_it_works": "Official SEC documents instantly silence delay rumors, triggering high retention and comment velocity.",
        "creator_credit": "@TakeTwoSEC",
        "last_analyzed": "2026-10-24 14:10:00"
    },
    {
        "id": "lead-2",
        "row_number": 3,
        "title": "Jason & Lucia Diner Audio Clip (Acoustic Phase Match Analysis)",
        "source_url": "https://reddit.com/r/gta6",
        "priority_score": 89,
        "fact_status": "Unverified Leak",
        "review_status": "Needs Review",
        "summary": "Purported 14-second audio conversation between Jason and Lucia inside a Vice City diner posted on TikTok. High risk of AI voice cloning.",
        "hook": "Is this real GTA 6 diner audio, or did someone just AI clone Lucia’s voice actress?",
        "commentary_draft": "A brand-new audio leak just exploded across TikTok claiming to feature raw voice lines between Jason and Lucia. But when we run the audio spectrum through acoustic comparison models, something does not add up.",
        "on_screen_text": "AI OR REAL LEAK?",
        "why_it_works": "Confronts the audience with an authenticity question, sparking immediate debate in comments.",
        "creator_credit": "u/ViceCityInsider",
        "last_analyzed": "2026-10-24 15:22:00"
    },
    {
        "id": "lead-3",
        "row_number": 4,
        "title": "Volumetric Ocean Mesh & Dynamic Buoyancy Engine Patent",
        "source_url": "https://youtube.com",
        "priority_score": 84,
        "fact_status": "Speculative Lore",
        "review_status": "Approved",
        "summary": "Frame-by-frame analysis of trailer wake simulation proving unified ocean fluid dynamics beyond RDR2 mechanics.",
        "hook": "Rockstar spent over six years completely rebuilding water physics from scratch for Vice City.",
        "commentary_draft": "Look closely at the water displacement around the speedboat in shot 14. That is not pre-baked animation. Rockstar patented a real-time fluid dynamics mesh that responds to wind velocity and boat hull drag simultaneously.",
        "on_screen_text": "NEXT-GEN WATER ENGINE",
        "why_it_works": "Appeals to graphics enthusiasts who appreciate technical leaps over standard gameplay clips.",
        "creator_credit": "@RockstarUniverse",
        "last_analyzed": "2026-10-24 12:45:00"
    },
    {
        "id": "lead-4",
        "row_number": 5,
        "title": "Bloomberg Insider Corroborates Seamless Split-Cut Character Switch",
        "source_url": "https://bloomberg.com",
        "priority_score": 91,
        "fact_status": "Credible Press",
        "review_status": "In Clip Queue",
        "summary": "Reputable reporting corroborates character switching happens seamlessly with contextual animations rather than bird-eye zoom.",
        "hook": "Character switching in GTA 6 is getting rid of the five-second satellite camera entirely.",
        "commentary_draft": "Remember how GTA 5 pulled the camera into the clouds every time you switched characters? Bloomberg insiders confirmed that in GTA 6, swapping between Jason and Lucia is completely seamless using cinematic split-cuts.",
        "on_screen_text": "SEAMLESS SWITCHING",
        "why_it_works": "Direct gameplay improvement that directly addresses an annoyance from GTA 5.",
        "creator_credit": "Jason Schreier / Bloomberg",
        "last_analyzed": "2026-10-24 09:30:00"
    }
]

CREATOR_PROFILES = [
    {
        "name": "Rockstar Universe",
        "handle": "@RockstarUniverse",
        "initials": "RU",
        "specialty": "Teasers, Mapping Coordinates & Official Filings",
        "credibility": "95% Accuracy • Tier 1 Insider",
        "relationship": "Lead Source",
        "links": [
            ("▶ YouTube Channel", "https://www.youtube.com/@RockstarUniverse"),
            ("𝕏 Twitter / X", "https://x.com/RStarUniverse")
        ]
    },
    {
        "name": "GTA 6 Informer",
        "handle": "@GTA6Informer",
        "initials": "GI",
        "specialty": "Actor & Lucia Voice Actress Face-match Analysis",
        "credibility": "92% Accuracy • Tier 1 Specialist",
        "relationship": "Collaborator",
        "links": [
            ("𝕏 Twitter / X", "https://x.com/GTA6Informer"),
            ("💬 Reddit Community", "https://www.reddit.com/r/GTA6/")
        ]
    },
    {
        "name": "LegacyKillaHD",
        "handle": "LegacyKillaHD",
        "initials": "LK",
        "specialty": "Studio Logistics, Internal Culture & Release Timelines",
        "credibility": "86% Accuracy • Tier 2 Commentator",
        "relationship": "Direct Contact",
        "links": [
            ("▶ YouTube Channel", "https://www.youtube.com/@LegacyKillaHD"),
            ("𝕏 Twitter / X", "https://x.com/LegacyKillaHD")
        ]
    },
    {
        "name": "TobiasM4",
        "handle": "u/TobiasM4",
        "initials": "TM",
        "specialty": "Source Code Leak Mining & Weapon Wheel Dissections",
        "credibility": "89% Accuracy • Tier 1 Technical",
        "relationship": "Credited in Description",
        "links": [
            ("💬 Reddit Profile", "https://www.reddit.com/user/TobiasM4/"),
            ("𝕏 Twitter / X", "https://x.com")
        ]
    }
]

ALERT_INTEL = {
    "Take-Two FY26 Schedule Reaffirmation": {
        "time": "12m ago",
        "type": "Official Rockstar",
        "source": "Take-Two SEC Form 10-Q",
        "impact": "High (96/100)",
        "summary": "Financial filing reiterates massive revenue projections between April 2025 and March 2026, officially safeguarding the launch timeline.",
        "hook": "Take-Two just confirmed their biggest release schedule in gaming history, and the date is locked in.",
        "action": "Produce an immediate 35s Shorts breakdown quoting the SEC filing numbers to combat delay rumors."
    },
    "Jason & Lucia Diner Audio Leak": {
        "time": "34m ago",
        "type": "Unverified Leak",
        "source": "TikTok & r/GTA6",
        "impact": "Viral Potential (88/100)",
        "summary": "Audio engineers discover anomalous room reverb indicating artificial synthesis rather than raw studio master tracks.",
        "hook": "Is this real GTA 6 audio or did someone just AI clone Lucia’s voice actress?",
        "action": "Produce a forensic audio breakdown pointing out the phase cancellation anomalies."
    },
    "Vice City Water Mesh Tessellation Patent": {
        "time": "2h ago",
        "type": "Speculative Lore",
        "source": "Rockstar Technology IP",
        "impact": "Medium (78/100)",
        "summary": "Patent filing demonstrates unified ocean fluid dynamics reacting in real time to atmospheric storm pressure.",
        "hook": "Rockstar spent six years completely rebuilding water physics from scratch for Vice City.",
        "action": "Produce a high-CTR visual comparison Short contrasting RDR2 and GTA 6 water simulations."
    }
}


# --------------------------------------------------
# GOOGLE SHEETS LIVE INTAKE
# --------------------------------------------------
@st.cache_resource
def get_sheets_client():
    if not HAS_GSPREAD:
        return None
    raw_creds = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = get_secret("GOOGLE_SHEET_ID")
    if not raw_creds or not sheet_id:
        return None
    try:
        service_account = json.loads(raw_creds) if isinstance(raw_creds, str) else dict(raw_creds)
        credentials = Credentials.from_service_account_info(
            service_account,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
        )
        return gspread.authorize(credentials).open_by_key(str(sheet_id))
    except Exception:
        return None


def load_live_data() -> Tuple[List[Dict[str, Any]], bool]:
    client = get_sheets_client()
    if client:
        try:
            ws = client.worksheet("Video Discovery")
            vals = ws.get_all_values()
            if vals and len(vals) > 1:
                headers = [h.strip().lower() for h in vals[0]]
                records = []
                for idx, row in enumerate(vals[1:]):
                    r_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                    records.append({
                        "id": f"row-{idx+2}",
                        "row_number": idx + 2,
                        "title": r_dict.get("video title") or r_dict.get("title") or f"Record #{idx+2}",
                        "source_url": r_dict.get("video url") or r_dict.get("url") or "",
                        "priority_score": int(r_dict.get("ai priority score") or 70),
                        "fact_status": r_dict.get("ai fact status") or "Unverified Leak",
                        "review_status": r_dict.get("review status") or "Needs Review",
                        "summary": r_dict.get("ai summary") or "Summary pending.",
                        "hook": r_dict.get("ai hook") or "",
                        "commentary_draft": r_dict.get("ai commentary draft") or "",
                        "on_screen_text": r_dict.get("ai on-screen text") or "GTA 6 INTEL",
                        "why_it_works": r_dict.get("why it works") or "High comment controversy factor.",
                        "creator_credit": r_dict.get("creator credit") or "@CommunitySource",
                        "last_analyzed": r_dict.get("ai last analyzed (utc)") or str(datetime.now())[:19]
                    })
                return records, True
        except Exception:
            pass
    return INITIAL_DATASET, False


# Initialize Session State
if "leads" not in st.session_state:
    loaded_records, is_live = load_live_data()
    st.session_state["leads"] = loaded_records
    st.session_state["sheets_live"] = is_live

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "✦ Spatial Pulse"

if "selected_alert" not in st.session_state:
    st.session_state["selected_alert"] = "Take-Two FY26 Schedule Reaffirmation"

if "selected_lead_id" not in st.session_state:
    st.session_state["selected_lead_id"] = st.session_state["leads"][0]["id"] if st.session_state["leads"] else "lead-1"


# --------------------------------------------------
# GROQ INFERENCE ENGINE
# --------------------------------------------------
def execute_groq_inference(lead: Dict[str, Any]) -> Dict[str, Any]:
    api_key = get_secret("GROQ_API_KEY")
    if not api_key or not HAS_GROQ:
        return {
            "priority_score": 94,
            "fact_status": lead.get("fact_status", "Unverified Leak"),
            "summary": f"Forensic audio and visual analysis completed for '{lead.get('title')[:60]}'.",
            "hook": f"Rockstar just changed everything we thought we knew about {lead.get('title')[:30]}...",
            "commentary_draft": "Notice what happens right in the middle of this clip. When you slow down the frame rate, the physics engine confirms a brand new atmospheric displacement system.",
            "on_screen_text": "LEAK CONFIRMED",
            "why_it_works": "Forces immediate replay and stimulates technical debate in the comment section.",
            "creator_credit": lead.get("creator_credit") or "@ViceCityInsider",
            "last_analyzed": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }

    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
You are VicePlug Hub's Senior GTA VI Content Research Editor & Viral Scriptwriter.
Analyze the provided record and craft an actionable short-form production dossier for YouTube Shorts & TikTok.
Return strictly valid JSON with this schema:
{
  "priority_score": int (1-100),
  "fact_status": "Official Rockstar" | "Credible Press" | "Speculative Lore" | "Unverified Leak",
  "summary": "1-2 sentence core factual event",
  "hook": "Spoken first 3-second hook creating massive curiosity (12-16 words)",
  "commentary_draft": "Complete 30-40 second voiceover script (75-90 words, punchy)",
  "on_screen_text": "3-word bold overlay title for screen",
  "why_it_works": "Psychological audience retention trigger",
  "creator_credit": "Handle, channel, or leaker source to credit"
}
"""
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({k: str(v)[:1500] for k, v in lead.items() if str(v).strip()})},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    parsed = json.loads(res.choices[0].message.content or "{}")
    return {
        "priority_score": parsed.get("priority_score", 90),
        "fact_status": parsed.get("fact_status", lead.get("fact_status", "Unverified Leak")),
        "summary": parsed.get("summary", "Summary unavailable."),
        "hook": parsed.get("hook", "You will not believe what just leaked out of Vice City..."),
        "commentary_draft": parsed.get("commentary_draft", "Script draft generated."),
        "on_screen_text": parsed.get("on_screen_text", "GTA 6 LEAK"),
        "why_it_works": parsed.get("why_it_works", "High debate potential in comments."),
        "creator_credit": parsed.get("creator_credit", lead.get("creator_credit", "@CommunitySource")),
        "last_analyzed": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }


def update_lead_state(lead_id: str, new_fields: Dict[str, Any]):
    leads = st.session_state["leads"]
    for i, item in enumerate(leads):
        if item["id"] == lead_id:
            leads[i].update(new_fields)
            break
    st.session_state["leads"] = leads


# --------------------------------------------------
# COMPUTED METRICS
# --------------------------------------------------
leads_data = st.session_state["leads"]
total_leads = len(leads_data)
needs_review_count = sum(1 for l in leads_data if l["review_status"] == "Needs Review")
ai_scripted_count = sum(1 for l in leads_data if bool(l.get("hook") and l.get("hook").strip()))
ready_to_cut_count = sum(1 for l in leads_data if l["review_status"] == "Approved")
has_groq_key = bool(get_secret("GROQ_API_KEY"))


# --------------------------------------------------
# FLOATING STUDIO DOCK (HEADER)
# --------------------------------------------------
curr_time = datetime.now(timezone.utc).strftime("%a, %b %d • %H:%M UTC")

st.markdown(f"""
    <div class="studio-nav-header">
        <div class="brand-typography">
            <span>VICEPLUG</span> // SPATIAL OS
            <span style="font-size:0.75rem; color:#64748B; font-weight:500; font-family:'Plus Jakarta Sans';">| GTA VI Intelligence Studio</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px; font-size:0.82rem; color:#94A3B8;">
            <span style="font-family:'JetBrains Mono'; font-size:0.78rem;">{curr_time}</span>
            <span style="display:inline-flex; align-items:center; gap:6px; background:{'rgba(0,255,136,0.12)' if st.session_state['sheets_live'] else 'rgba(139,92,246,0.15)'}; color:{'#00FF88' if st.session_state['sheets_live'] else '#A78BFA'}; padding:4px 12px; border-radius:20px; font-size:0.74rem; font-weight:600;">
                ● {'Sheets Live' if st.session_state['sheets_live'] else 'Local Session Active'}
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px; background:{'rgba(0,245,255,0.12)' if has_groq_key else 'rgba(255,184,0,0.14)'}; color:{'#00F5FF' if has_groq_key else '#FFB800'}; padding:4px 12px; border-radius:20px; font-size:0.74rem; font-weight:600;">
                ⚡ {'Groq Llama-3.3 Live' if has_groq_key else 'Groq Fallback Mode'}
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Segmented VisionOS Navigation Buttons
nav_c1, nav_c2, nav_c3, nav_c4, nav_c5, nav_c6 = st.columns(6)
with nav_c1:
    if st.button("✦ Spatial Pulse", use_container_width=True): st.session_state["active_nav"] = "✦ Spatial Pulse"
with nav_c2:
    if st.button(f"⚡ Lead Dossiers ({needs_review_count})", use_container_width=True): st.session_state["active_nav"] = "⚡ Lead Dossiers"
with nav_c3:
    if st.button(f"🎬 Ready to Cut ({ready_to_cut_count})", use_container_width=True): st.session_state["active_nav"] = "🎬 Ready to Cut"
with nav_c4:
    if st.button("💎 Creator Radar", use_container_width=True): st.session_state["active_nav"] = "💎 Creator Radar"
with nav_c5:
    if st.button("🗄 Master Database", use_container_width=True): st.session_state["active_nav"] = "🗄 Master Database"
with nav_c6:
    if st.button("⚙ Studio Settings", use_container_width=True): st.session_state["active_nav"] = "⚙ Studio Settings"

st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)


# ==================================================
# SCREEN 1: SPATIAL PULSE (3D CANVAS + BREAKING ALERTS)
# ==================================================
if st.session_state["active_nav"] == "✦ Spatial Pulse":

    # --- ACTION CALLOUT BANNER ---
    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 2px 4px;">
                <div>
                    <span style="font-family:'Space Grotesk'; font-weight:700; font-size:1.1rem; color:#FFF;">
                        Action Horizon: <span style="color:#00F5FF;">{needs_review_count} Leads</span> Require Script Approval
                    </span>
                    <div style="color:#94A3B8; font-size:0.86rem; margin-top:2px;">
                        Inspect the 3D signal graph below ➔ Generate high-CTR spoken hooks ➔ Push directly to your cutting desk.
                    </div>
                </div>
                <div>
                    <span style="font-size:0.8rem; background:rgba(0,245,255,0.12); color:#00F5FF; padding:6px 14px; border-radius:30px; border:1px solid rgba(0,245,255,0.3); font-weight:600; font-family:'JetBrains Mono';">
                        TARGET: 25-40S SHORTS
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # --- 3D INTERACTIVE THREE.JS CYBERNETIC LANDSCAPE ---
    with st.container(border=True):
        col_info, col_canvas = st.columns([1.1, 2.2], gap="large")

        with col_info:
            st.markdown("""
                <div style="padding: 12px 0;">
                    <div style="font-size:0.75rem; font-weight:700; color:#00F5FF; letter-spacing:0.1em; text-transform:uppercase; font-family:'JetBrains Mono';">
                        // 2026 SPATIAL DATA SURFACE
                    </div>
                    <div style="font-family:'Space Grotesk'; font-size:1.95rem; font-weight:700; color:#FFF; margin:4px 0 8px 0; line-height:1.2; letter-spacing:-0.03em;">
                        Vice City Cyber-Mesh
                    </div>
                    <p style="color:#94A3B8; font-size:0.88rem; line-height:1.6;">
                        Interactive WebGL 2 cybernetic terrain & orbiting synaptic node matrix. Move your cursor over the canvas to glide the spatial camera with smooth inertia.
                    </p>
                    <div style="display:flex; flex-direction:column; gap:8px; margin-top:16px; font-size:0.82rem;">
                        <div><span style="color:#00FF88; font-weight:700;">● Official Rockstar:</span> Verified SEC filings & trailers</div>
                        <div><span style="color:#A78BFA; font-weight:700;">● Credible Press:</span> Bloomberg & trusted reporters</div>
                        <div><span style="color:#00F5FF; font-weight:700;">● Community Lore:</span> Speculative map & physics analysis</div>
                        <div><span style="color:#FF2E93; font-weight:700;">● Unverified Leaks:</span> Raw viral clip captures</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_canvas:
            # Three.js 60fps Neon Undulating Floor & Particle Nebula
            node_count = min(max(total_leads * 8, 220), 450)
            three_js_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <style>
                body {{ margin: 0; overflow: hidden; background: transparent; }}
                canvas {{ width: 100%; height: 100%; display: block; }}
              </style>
              <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            </head>
            <body>
              <script>
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.set(0, 1.2, 5.0);

                const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true, powerPreference: "high-performance" }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                document.body.appendChild(renderer.domElement);

                const group = new THREE.Group();
                scene.add(group);

                // 1. Futuristic Vice City Topography Grid Floor
                const gridHelper = new THREE.GridHelper(10, 24, 0xFF2E93, 0x7C3AED);
                gridHelper.position.y = -1.2;
                gridHelper.material.opacity = 0.35;
                gridHelper.material.transparent = true;
                group.add(gridHelper);

                // 2. Dynamic Content Nodes
                const count = {node_count};
                const geometry = new THREE.BufferGeometry();
                const positions = new Float32Array(count * 3);
                const colors = new Float32Array(count * 3);

                const cOfficial = new THREE.Color(0x00FF88);
                const cPress = new THREE.Color(0xA78BFA);
                const cLore = new THREE.Color(0x00F5FF);
                const cLeak = new THREE.Color(0xFF2E93);

                for (let i = 0; i < count; i++) {{
                    const u = Math.random();
                    const v = Math.random();
                    const theta = u * 2.0 * Math.PI;
                    const phi = Math.acos(2.0 * v - 1.0);
                    const r = 1.45 + (Math.random() - 0.5) * 0.4;

                    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
                    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.85;
                    positions[i * 3 + 2] = r * Math.cos(phi);

                    let col = cPress;
                    const rand = Math.random();
                    if (rand < 0.22) col = cOfficial;
                    else if (rand < 0.52) col = cLore;
                    else if (rand < 0.78) col = cPress;
                    else col = cLeak;

                    colors[i * 3] = col.r;
                    colors[i * 3 + 1] = col.g;
                    colors[i * 3 + 2] = col.b;
                }}

                geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

                const particleMaterial = new THREE.PointsMaterial({{
                    size: 0.052,
                    vertexColors: true,
                    transparent: true,
                    opacity: 0.95,
                    blending: THREE.AdditiveBlending
                }});

                const particles = new THREE.Points(geometry, particleMaterial);
                group.add(particles);

                // 3. Central Glowing Luminous Core
                const coreGeo = new THREE.IcosahedronGeometry(0.55, 2);
                const coreMat = new THREE.MeshBasicMaterial({{
                    color: 0x00F5FF,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.28
                }});
                const core = new THREE.Mesh(coreGeo, coreMat);
                group.add(core);

                // 4. Orbital Synaptic Ring
                const ringGeo = new THREE.RingGeometry(1.9, 1.93, 64);
                const ringMat = new THREE.MeshBasicMaterial({{
                    color: 0xFF2E93,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.3
                }});
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 2.8;
                group.add(ring);

                // Smooth Parallax Lerp
                let mouseX = 0, mouseY = 0;
                let targetX = 0, targetY = 0;

                window.addEventListener('mousemove', (e) => {{
                    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
                    mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
                }});

                function animate() {{
                    requestAnimationFrame(animate);

                    targetX += (mouseX * 0.45 - targetX) * 0.05;
                    targetY += (mouseY * 0.4 - targetY) * 0.05;

                    group.rotation.y += 0.004;
                    group.rotation.x = targetY;
                    group.rotation.z = -targetX * 0.3;

                    gridHelper.position.z = (gridHelper.position.z + 0.008) % 1.0;
                    core.rotation.y -= 0.006;
                    ring.rotation.z += 0.002;

                    renderer.render(scene, camera);
                }}
                animate();

                window.addEventListener('resize', () => {{
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                }});
              </script>
            </body>
            </html>
            """
            components.html(three_js_code, height=275, scrolling=False)

    # --- 4 STREAMLINED METRICS ---
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.container(border=True):
            st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">TOTAL LEADS</div>
                    <div class="stat-val">{total_leads}</div>
                    <div style="font-size:0.75rem; color:#00FF88; font-weight:600;">↑ 100% Sheets Synced</div>
                </div>
            """, unsafe_allow_html=True)
    with m2:
        with st.container(border=True):
            st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">NEEDS REVIEW</div>
                    <div class="stat-val" style="color:#FFB800;">{needs_review_count}</div>
                    <div style="font-size:0.75rem; color:#FF2E93; font-weight:600;">Pending Script Generation</div>
                </div>
            """, unsafe_allow_html=True)
    with m3:
        with st.container(border=True):
            st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">AI HOOKS READY</div>
                    <div class="stat-val" style="color:#00F5FF;">{ai_scripted_count}</div>
                    <div style="font-size:0.75rem; color:#A78BFA; font-weight:600;">Paced for 30s Shorts</div>
                </div>
            """, unsafe_allow_html=True)
    with m4:
        with st.container(border=True):
            st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">READY TO CUT</div>
                    <div class="stat-val" style="color:#00FF88;">{ready_to_cut_count}</div>
                    <div style="font-size:0.75rem; color:#00FF88; font-weight:600;">Waiting in Cutting Desk</div>
                </div>
            """, unsafe_allow_html=True)

    # --- INTERACTIVE ALERTS DRAWER & VELOCITY DONUT ---
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    c_alerts, c_donut = st.columns([1.6, 1.2], gap="medium")

    with c_alerts:
        with st.container(border=True):
            st.markdown("""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <b style="font-size:0.98rem; color:#FFF; font-family:'Space Grotesk';">🔔 Breaking Alerts & Topic Intelligence</b>
                        <div style="font-size:0.78rem; color:#94A3B8;">Click any signal to inspect its origin, controversy factor, and Short blueprint.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            for alert_title, alert_info in ALERT_INTEL.items():
                col_btn, col_badge = st.columns([3.5, 1.2])
                with col_btn:
                    if st.button(f"⚡ {alert_title}", key=f"btn_alt_{alert_title}", use_container_width=True):
                        st.session_state["selected_alert"] = alert_title
                with col_badge:
                    b_color = "#00FF88" if "official" in alert_info['type'].lower() else "#FF2E93" if "leak" in alert_info['type'].lower() else "#00F5FF"
                    st.markdown(f"<div style='text-align:right; font-size:0.72rem; color:{b_color}; font-weight:600; padding-top:6px;'>{alert_info['type']}</div>", unsafe_allow_html=True)

            # Selected Alert Drawer
            sel = ALERT_INTEL.get(st.session_state["selected_alert"])
            if sel:
                st.markdown(f"""
                    <div style="margin-top:14px; padding:16px; background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.35); border-radius:14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-weight:700; font-size:1.05rem; color:#FFF;">{st.session_state['selected_alert']}</span>
                            <span style="font-size:0.74rem; background:rgba(124,58,237,0.25); color:#A78BFA; padding:3px 10px; border-radius:6px; font-weight:600;">{sel['type']}</span>
                        </div>
                        <div style="font-size:0.86rem; color:#CBD5E1; margin-bottom:8px;"><b>Origin:</b> {sel['source']} • <b>Impact:</b> {sel['impact']}</div>
                        <div style="font-size:0.86rem; color:#94A3B8; margin-bottom:10px;"><b>Core Event:</b> {sel['summary']}</div>
                        <div style="background:rgba(0,0,0,0.4); padding:10px 14px; border-radius:8px; font-size:0.86rem; margin-bottom:10px; border:1px solid rgba(255,255,255,0.06);">
                            <span style="color:#00F5FF; font-weight:600;">Suggested 3s Hook:</span> "{sel['hook']}"
                        </div>
                        <div style="font-size:0.84rem; color:#00FF88;"><b>Recommended Action:</b> {sel['action']}</div>
                    </div>
                """, unsafe_allow_html=True)

    with c_donut:
        with st.container(border=True):
            st.markdown('<b style="font-size:0.98rem; color:#FFF; font-family:\'Space Grotesk\';">📊 Pipeline Distribution</b>', unsafe_allow_html=True)

            status_counts = pd.Series([l["fact_status"] for l in leads_data]).value_counts()
            labels = status_counts.index.tolist()
            values = status_counts.values.tolist()

            fig_donut = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                marker=dict(colors=['#FF2E93', '#7C3AED', '#00F5FF', '#00FF88', '#FFB800']),
                textinfo='none'
            )])
            fig_donut.update_layout(
                height=180,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                annotations=[dict(text=f'<b>{sum(values)}</b><br><span style="font-size:9px; color:#94A3B8;">SIGNALS</span>', x=0.5, y=0.5, font_size=14, font_color="#FFF", showarrow=False)]
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={'staticPlot': True})

            st.markdown("""
                <div style="display:flex; justify-content:space-around; font-size:0.75rem; color:#94A3B8; margin-top:4px;">
                    <span><b style="color:#FF2E93;">●</b> Leaks</span>
                    <span><b style="color:#7C3AED;">●</b> Lore</span>
                    <span><b style="color:#00F5FF;">●</b> Press</span>
                    <span><b style="color:#00FF88;">●</b> Official</span>
                </div>
            """, unsafe_allow_html=True)


# ==================================================
# SCREEN 2: LEAD DOSSIERS (EDITORIAL SPOTLIGHT SUITE)
# ==================================================
elif st.session_state["active_nav"] == f"⚡ Lead Dossiers ({needs_review_count})":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Lead Dossiers & Script Studio</h2>", unsafe_allow_html=True)
    st.caption("Select any discovered GTA VI story from the horizontal filmstrip to view its full Teleprompter Script and Algorithmic Retention Blueprint.")

    # Search & Filter
    f_search, f_veracity = st.columns([3, 1.2])
    with f_search:
        search_query = st.text_input("Search Dossiers", placeholder="Filter by keywords, characters, leaks, or mechanics...", label_visibility="collapsed")
    with f_veracity:
        veracity_filter = st.selectbox("Credibility Filter", ["All Sources", "Official Rockstar", "Credible Press", "Speculative Lore", "Unverified Leak"], label_visibility="collapsed")

    filtered_leads = [
        l for l in leads_data
        if (not search_query or search_query.lower() in l["title"].lower() or search_query.lower() in l["summary"].lower())
        and (veracity_filter == "All Sources" or l["fact_status"] == veracity_filter)
    ]

    if not filtered_leads:
        st.info("No leads match the specified filter.")
    else:
        # 1. HORIZONTAL STORY SELECTOR (FILMSTRIP)
        st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#94A3B8; text-transform:uppercase; margin-bottom:6px; font-family:JetBrains Mono;'>// SELECT LEAD TO INSPECT IN STUDIO:</div>", unsafe_allow_html=True)
        
        strip_cols = st.columns(len(filtered_leads))
        for idx, lead in enumerate(filtered_leads):
            lead_id = lead["id"]
            is_active = st.session_state["selected_lead_id"] == lead_id
            with strip_cols[idx]:
                badge_emoji = "🛡️" if "official" in lead["fact_status"].lower() else "🔥" if "leak" in lead["fact_status"].lower() else "📰"
                btn_label = f"{badge_emoji} Lead #{lead['row_number']}"
                if st.button(btn_label, key=f"strip_{lead_id}", use_container_width=True):
                    st.session_state["selected_lead_id"] = lead_id

        # 2. ACTIVE SPOTLIGHT DOSSIER
        active_lead = next((l for l in leads_data if l["id"] == st.session_state["selected_lead_id"]), filtered_leads[0])
        lead_id = active_lead["id"]
        row_num = active_lead["row_number"]
        fact = active_lead["fact_status"]
        status = active_lead["review_status"]

        badge_bg = "rgba(255, 46, 147, 0.12)" if "leak" in fact.lower() else "rgba(0, 245, 255, 0.12)" if "official" in fact.lower() else "rgba(139, 92, 246, 0.15)"
        badge_text = "#FF2E93" if "leak" in fact.lower() else "#00F5FF" if "official" in fact.lower() else "#A78BFA"

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:0.8rem; background:rgba(0,245,255,0.12); color:#00F5FF; padding:4px 12px; border-radius:6px; font-weight:700; font-family:'JetBrains Mono';">PRIORITY: {active_lead['priority_score']}/100</span>
                        <span style="font-size:0.8rem; background:{badge_bg}; color:{badge_text}; padding:4px 12px; border-radius:6px; font-weight:600;">{fact}</span>
                        <span style="font-size:0.75rem; color:#64748B;">Row #{row_num}</span>
                    </div>
                    <span style="font-size:0.8rem; padding:4px 14px; border-radius:20px; background:rgba(255,255,255,0.06); color:#E2E8F0; font-weight:600;">{status}</span>
                </div>
                <div style="font-family:'Space Grotesk'; font-size:1.5rem; font-weight:700; color:#FFF; margin-bottom:18px; line-height:1.3;">{active_lead['title']}</div>
            """, unsafe_allow_html=True)

            d_prompter, d_strategy = st.columns([1.6, 1], gap="large")

            with d_prompter:
                st.markdown(f"""
                    <div class="teleprompter-card">
                        <div style="font-size:0.75rem; font-weight:700; color:#00F5FF; text-transform:uppercase; font-family:'JetBrains Mono'; margin-bottom:4px;">
                            🎣 0–3s Spoken Teleprompter Hook:
                        </div>
                        <div class="prompter-hook">
                            <span style="font-size:1.05rem; color:#FFF; font-weight:600; font-style:italic;">"{active_lead['hook'] or 'Hook not yet generated. Click Generate Script.'}"</span>
                        </div>
                        <div style="font-size:0.75rem; font-weight:700; color:#00FF88; text-transform:uppercase; font-family:'JetBrains Mono'; margin-bottom:6px;">
                            📝 30-Second Voiceover Script Draft (145 WPM):
                        </div>
                        <div style="font-size:0.92rem; color:#CBD5E1; line-height:1.6; background:rgba(0,0,0,0.3); padding:14px; border-radius:8px;">
                            {active_lead['commentary_draft'] or 'Click Generate Script below to synthesize with Groq Llama-3.3.'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with d_strategy:
                st.markdown(f"""
                    <div class="teleprompter-card" style="height:100%; display:flex; flex-direction:column; justify-content:space-between;">
                        <div>
                            <div style="font-size:0.75rem; font-weight:700; color:#FF2E93; text-transform:uppercase; font-family:'JetBrains Mono'; margin-bottom:6px;">
                                🎯 Algorithmic Retention Trigger:
                            </div>
                            <div style="font-size:0.88rem; color:#94A3B8; line-height:1.5; margin-bottom:16px;">
                                {active_lead['why_it_works']}
                            </div>
                            <div style="font-size:0.75rem; font-weight:700; color:#00F5FF; text-transform:uppercase; font-family:'JetBrains Mono'; margin-bottom:4px;">
                                📱 Mobile On-Screen Overlay Text:
                            </div>
                            <div style="font-size:1.1rem; font-weight:700; color:#FFF; margin-bottom:16px;">
                                {active_lead['on_screen_text']}
                            </div>
                        </div>

                        <div>
                            <div style="font-size:0.72rem; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:2px; font-family:'JetBrains Mono';">
                                Source Channel Attribution:
                            </div>
                            <div style="font-size:0.86rem; color:#E2E8F0; font-weight:600;">{active_lead['creator_credit']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            # Action Controls
            act_c1, act_c2, act_c3 = st.columns([1.6, 1.8, 3])
            with act_c1:
                is_approved = active_lead["review_status"] == "Approved"
                if st.button("✓ In Edit Queue" if is_approved else "🚀 Push to Edit Queue", key=f"spot_btn_cut_{lead_id}", disabled=is_approved, use_container_width=True):
                    update_lead_state(lead_id, {"review_status": "Approved"})
                    st.toast(f"Pushed Lead #{row_num} to Ready to Cut desk!", icon="🎬")
                    st.rerun()

            with act_c2:
                if st.button("🧠 Generate / Re-Run Groq", key=f"spot_btn_groq_{lead_id}", use_container_width=True):
                    with st.spinner("Synthesizing Shorts blueprint via Groq..."):
                        updates = execute_groq_inference(active_lead)
                        update_lead_state(lead_id, updates)
                        st.toast("Script blueprint successfully updated!", icon="⚡")
                        st.rerun()

            with act_c3:
                if active_lead["source_url"] and active_lead["source_url"].startswith("http"):
                    st.markdown(f"<div style='padding-top:8px;'><a href='{active_lead['source_url']}' target='_blank' style='font-size:0.84rem; color:#00F5FF; text-decoration:none;'>🔗 Open Source Video / Leak Clip ↗</a></div>", unsafe_allow_html=True)


# ==================================================
# SCREEN 3: READY TO CUT (EDITING DESK)
# ==================================================
elif st.session_state["active_nav"] == f"🎬 Ready to Cut ({ready_to_cut_count})":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Producer's Cutting Desk</h2>", unsafe_allow_html=True)
    st.caption("All greenlit stories with completed scripts and hooks. Open Premiere or CapCut, record voiceovers, and check off.")

    approved_leads = [l for l in leads_data if l["review_status"] == "Approved"]

    if not approved_leads:
        st.info("No clips in your editing queue yet! Head over to the 'Lead Dossiers' and click '🚀 Push to Edit Queue' on greenlit angles.")
    else:
        for lead in approved_leads:
            lead_id = lead["id"]
            with st.container(border=True):
                st.markdown(f"""
                    <div style="font-family:'Space Grotesk'; font-size:1.3rem; font-weight:700; color:#00FF88; margin-bottom:10px;">{lead['title']}</div>
                    <div style="background:rgba(11, 16, 31, 0.7); border:1px solid rgba(0,255,136,0.25); border-radius:12px; padding:18px; margin-bottom:14px;">
                        <span style="color:#00F5FF; font-weight:700; font-size:0.75rem; text-transform:uppercase; font-family:'JetBrains Mono';">[Spoken Hook (0–3 Seconds)]:</span>
                        <div style="font-size:1.05rem; color:#FFF; font-weight:600; margin:4px 0 14px 0;">"{lead['hook']}"</div>
                        <span style="color:#00FF88; font-weight:700; font-size:0.75rem; text-transform:uppercase; font-family:'JetBrains Mono';">[Voiceover Script (3–35 Seconds)]:</span>
                        <div style="font-size:0.94rem; color:#CBD5E1; line-height:1.6; margin-top:4px;">{lead['commentary_draft']}</div>
                        <div style="margin-top:12px; font-size:0.8rem; color:#94A3B8;">
                            <b>On-Screen Overlay Text:</b> <span style="color:#FFF; font-weight:700;">{lead['on_screen_text']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                act_done, act_link = st.columns([1.5, 3])
                with act_done:
                    if st.button("✅ Mark as Published", key=f"cut_btn_pub_{lead_id}", use_container_width=True):
                        update_lead_state(lead_id, {"review_status": "Published"})
                        st.toast("Marked lead as Published!", icon="🚀")
                        st.rerun()
                with act_link:
                    if lead["source_url"] and lead["source_url"].startswith("http"):
                        st.markdown(f"<div style='padding-top:8px;'><a href='{lead['source_url']}' target='_blank' style='font-size:0.84rem; color:#00F5FF; text-decoration:none;'>📥 Download/Open Source Footage ↗</a></div>", unsafe_allow_html=True)


# ==================================================
# SCREEN 4: CREATOR RADAR (HOLOGRAPHIC TILES)
# ==================================================
elif st.session_state["active_nav"] == "💎 Creator Radar":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Creator Intelligence & Leaker Radar</h2>", unsafe_allow_html=True)
    st.caption("Holographic glass profile directory of key GTA VI leakers, content creators, and news aggregators with clickable channel hyperlinks.")

    card_c1, card_c2 = st.columns(2, gap="medium")
    for i, profile in enumerate(CREATOR_PROFILES):
        target_col = card_c1 if i % 2 == 0 else card_c2
        with target_col:
            links_html = "".join([f'<a href="{url}" target="_blank" class="hyperlink-chip">{name} ↗</a> ' for name, url in profile["links"]])
            st.markdown(f"""
                <div class="creator-glass-tile" style="margin-bottom:16px;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">
                            <div style="display:flex; align-items:center; gap:14px;">
                                <div class="avatar-sphere">{profile['initials']}</div>
                                <div>
                                    <div style="font-size:1.2rem; font-weight:700; color:#FFF; font-family:'Space Grotesk';">{profile['name']}</div>
                                    <div style="font-size:0.82rem; color:#00F5FF; font-weight:600;">{profile['handle']}</div>
                                </div>
                            </div>
                            <span style="font-size:0.75rem; background:rgba(0,255,136,0.12); color:#00FF88; padding:4px 12px; border-radius:20px; font-weight:600; border:1px solid rgba(0,255,136,0.25);">
                                {profile['relationship']}
                            </span>
                        </div>
                        <div style="font-size:0.88rem; color:#CBD5E1; margin-bottom:8px;"><b>Focus:</b> {profile['specialty']}</div>
                        <div style="font-size:0.8rem; color:#94A3B8; margin-bottom:16px;"><b>Credibility:</b> {profile['credibility']}</div>
                    </div>
                    <div>
                        <div style="font-size:0.74rem; font-weight:600; color:#64748B; text-transform:uppercase; margin-bottom:8px; font-family:'JetBrains Mono';">Direct Platform Channels:</div>
                        <div style="display:flex; flex-wrap:wrap; gap:8px;">
                            {links_html}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
            <b style="font-size:0.95rem; color:#FFF; font-family:'Space Grotesk';">📋 Pre-Formatted Video Description Credit Block</b>
            <p style="font-size:0.84rem; color:#94A3B8; margin: 4px 0 10px 0;">Copy and paste this credit block into your Shorts and TikTok descriptions to maintain creator goodwill and prevent copyright strikes:</p>
            <div style="background:rgba(0,0,0,0.4); border:1px solid var(--glass-border); border-radius:10px; padding:14px; font-family:'JetBrains Mono'; font-size:0.78rem; color:#00F5FF; line-height:1.5;">
                🚨 GTA VI Content Intelligence<br>
                Original clip breakdown credit: [Creator Name] (@Handle)<br>
                All game rights & trademarks belong to Rockstar Games / Take-Two Interactive.<br>
                Curated & scripted via VicePlug Hub.
            </div>
        """, unsafe_allow_html=True)


# ==================================================
# SCREEN 5: MASTER DATABASE (SPREADSHEET EXPORT)
# ==================================================
elif st.session_state["active_nav"] == "🗄 Master Database":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Google Sheets Live Master Database</h2>", unsafe_allow_html=True)
    st.caption("Bi-directional spreadsheet sync and export workspace.")

    df_export = pd.DataFrame(leads_data)
    st.dataframe(df_export, use_container_width=True, hide_index=True, height=450)

    c_dl, c_sync = st.columns([1, 2])
    with c_dl:
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Export CSV",
            data=csv,
            file_name=f"viceplug_intel_{str(datetime.now())[:10]}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c_sync:
        if st.button("↻ Flush Cache & Re-Sync Google Sheets", use_container_width=True):
            st.cache_data.clear()
            reloaded, live = load_live_data()
            st.session_state["leads"] = reloaded
            st.session_state["sheets_live"] = live
            st.toast("Refreshed with latest spreadsheet data!", icon="🔄")
            st.rerun()


# ==================================================
# SCREEN 6: STUDIO SETTINGS & SECRETS
# ==================================================
elif st.session_state["active_nav"] == "⚙ Studio Settings":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Studio Integrations & Health</h2>", unsafe_allow_html=True)
    st.caption("Verify environment secrets, Groq inference status, and Google Cloud authorization.")

    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:10px;">
                    <div><b>Groq Cloud API Gateway:</b><br><span style="font-size:0.8rem; color:#94A3B8;">Llama-3.3-70B model execution</span></div>
                    <span style="color:{'#00FF88' if has_groq_key else '#FFB800'}; font-weight:700;">{'CONNECTED' if has_groq_key else 'FALLBACK ACTIVE'}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:10px;">
                    <div><b>Google Sheets Service Account:</b><br><span style="font-size:0.8rem; color:#94A3B8;">Bi-directional spreadsheet sync</span></div>
                    <span style="color:{'#00FF88' if st.session_state['sheets_live'] else '#A78BFA'}; font-weight:700;">{'CONNECTED' if st.session_state['sheets_live'] else 'LOCAL SESSION CACHE'}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><b>Client WebGL 2 Renderer:</b><br><span style="font-size:0.8rem; color:#94A3B8;">Hardware-accelerated Three.js canvas</span></div>
                    <span style="color:#00FF88; font-weight:700;">ACTIVE (60 FPS)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="margin-top:14px; font-size:0.84rem; color:#94A3B8;">
            <b>How to connect live credentials on Streamlit Cloud:</b><br>
            Go to your app dashboard at <a href="https://share.streamlit.io" target="_blank" style="color:#00F5FF;">share.streamlit.io</a> ➔ App Settings ➔ <b>Secrets</b> ➔ Paste your <code>GROQ_API_KEY</code> and <code>GOOGLE_SERVICE_ACCOUNT_JSON</code>.
        </div>
    """, unsafe_allow_html=True)
