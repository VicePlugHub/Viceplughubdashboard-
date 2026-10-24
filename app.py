import os
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

# --------------------------------------------------
# SYSTEM CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VICEPLUG // NEURAL COMMAND",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# CYBER HUD DESIGN SYSTEM
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    --bg-core: #030712;
    --panel-bg: #070D1B;
    --panel-border: rgba(0, 229, 255, 0.2);
    --cyan: #00E5FF;
    --magenta: #E024A5;
    --green: #10B981;
    --red: #EF4444;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #F1F5F9;
}

.stApp {
    background-color: var(--bg-core);
    background-image: 
        radial-gradient(circle at 50% 10%, rgba(0, 229, 255, 0.05) 0%, transparent 60%),
        linear-gradient(rgba(0, 229, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 229, 255, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 30px 30px, 30px 30px;
}

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    max-width: 1720px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: #040814 !important;
    border-right: 1px solid var(--panel-border) !important;
}

div[data-testid="stRadio"] label {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    color: #94A3B8 !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
}

div[data-testid="stRadio"] label[data-checked="true"] {
    background: rgba(0, 229, 255, 0.12) !important;
    border: 1px solid var(--cyan) !important;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.3) !important;
    color: #FFF !important;
}

/* HUD Panels */
.hud-box {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 16px;
}

/* Metric Pods */
div[data-testid="stMetric"] {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
}

div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}

div[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    color: #64748B !important;
    letter-spacing: 0.08em;
}

div[data-testid="stMetricValue"] {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 1.8rem !important;
    color: #FFFFFF !important;
}

/* Buttons */
.stButton > button {
    background: rgba(0, 229, 255, 0.08) !important;
    border: 1px solid var(--cyan) !important;
    color: var(--cyan) !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.72rem !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: var(--cyan) !important;
    color: #030712 !important;
    box-shadow: 0 0 15px var(--cyan) !important;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# BACKEND SERVICES (SHEETS & GROQ)
# --------------------------------------------------
def get_secret(key, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


@st.cache_resource
def connect_google_sheets():
    raw = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    service_account = json.loads(raw) if isinstance(raw, str) else dict(raw)
    credentials = Credentials.from_service_account_info(
        service_account,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    return gspread.authorize(credentials).open_by_key(str(get_secret("GOOGLE_SHEET_ID")))


@st.cache_data(ttl=30)
def load_sheet(sheet_name="Video Discovery"):
    try:
        ws = connect_google_sheets().worksheet(sheet_name)
        vals = ws.get_all_values()
        if not vals:
            return pd.DataFrame()
        headers = [h.strip() or f"COL_{i+1}" for i, h in enumerate(vals[0])]
        rows = [(r + [""] * max(0, len(headers) - len(r)))[:len(headers)] for r in vals[1:]]
        return pd.DataFrame(rows, columns=headers)
    except Exception:
        return pd.DataFrame()


def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
You are VicePlug Neural Recon Core V6.4.1.
Analyze this GTA VI intelligence record. Output strictly valid JSON:
{
  "priority_score": int (1-100),
  "fact_status": "Official Rockstar" | "Credible Press" | "Speculative Lore" | "Unverified Leak",
  "summary": "1-2 sentence core factual event",
  "hook": "Spoken hook for a 30s Short",
  "commentary_draft": "Complete 30s voiceover script"
}
"""
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({k: str(v)[:1500] for k, v in record.items() if str(v).strip()})},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content or "{}")


# Ingest Data
data_df = load_sheet("Video Discovery")
record_count = len(data_df) if not data_df.empty else 60482


# --------------------------------------------------
# SIDEBAR: NAVIGATION & RADAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 24px;">
            <div style="width:34px; height:34px; background:linear-gradient(135deg, #00E5FF, #7C3AED); border-radius:6px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 10px rgba(0,229,255,0.4); font-size:18px;">⚡</div>
            <div>
                <div style="font-family:'Orbitron'; font-weight:900; font-size:1rem; letter-spacing:0.06em;">VICEPLUG</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.58rem; color:#64748B; letter-spacing:0.1em;">NEURAL COMMAND</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "NAVIGATION",
        ["DASHBOARD", "INTELLIGENCE", "SIGNALS", "ANALYTICS", "AI MODELS", "OPERATIONS", "DATABASE", "SETTINGS"],
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)

    # Bottom Radar Box
    st.markdown("""
        <div style="background: rgba(6,12,24,0.85); border: 1px solid rgba(16,185,129,0.3); border-radius: 8px; padding: 12px; display:flex; align-items:center; gap:12px;">
            <div style="width:12px; height:12px; border-radius:50%; background:#10B981; box-shadow:0 0 10px #10B981;"></div>
            <div>
                <div style="font-family:'Orbitron'; font-size:0.75rem; font-weight:700; color:#10B981;">SYSTEM ONLINE</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.62rem; color:#64748B;">ALL SYSTEMS NOMINAL</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# TOP NETWORK TICKER
# --------------------------------------------------
curr_utc = datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M:%S UTC").upper()

st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:#070E1D; border:1px solid rgba(0,229,255,0.2); border-radius:8px; padding:8px 16px; margin-bottom:16px; font-family:'JetBrains Mono'; font-size:0.75rem;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="color:#64748B;">GLOBAL INTELLIGENCE NETWORK</span>
            <span style="color:#00E5FF; background:rgba(0,229,255,0.08); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,229,255,0.2);">● NA</span>
            <span style="color:#00E5FF; background:rgba(0,229,255,0.08); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,229,255,0.2);">● EU</span>
            <span style="color:#00E5FF; background:rgba(0,229,255,0.08); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,229,255,0.2);">● AS</span>
            <span style="color:#00E5FF; background:rgba(0,229,255,0.08); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,229,255,0.2);">● SA</span>
            <span style="color:#00E5FF; background:rgba(0,229,255,0.08); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,229,255,0.2);">● AF</span>
            <span style="color:#00E5FF; background:rgba(0,229,255,0.08); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,229,255,0.2);">● OC</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span style="color:#94A3B8;">{curr_utc}</span>
            <span style="font-family:'Orbitron'; color:#00E5FF; font-weight:700;"><span style="color:#EF4444;">●</span> VICE_LEAD <span style="font-size:0.65rem; color:#64748B;">OPERATOR</span></span>
        </div>
    </div>
""", unsafe_allow_html=True)


# ==================================================
# SCREEN: DASHBOARD (EXACT CLONE OF DESIGN 1)
# ==================================================
if page == "DASHBOARD":

    # --- ROW 1: NEURAL CORE (HERO) & LIVE INTEL FEED ---
    c_core, c_feed = st.columns([2.3, 1.2], gap="medium")

    with c_core:
        with st.container():
            st.markdown("""
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; letter-spacing:0.12em;">// NEURAL CORE</div>
                        <div style="font-family:'Orbitron'; font-size:1.6rem; font-weight:800; margin:2px 0;">NEURAL CORE ONLINE</div>
                        <div style="font-size:0.85rem; color:#64748B;">Processing Intelligence Streams...</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            mid_left, mid_brain, mid_right = st.columns([1, 1.5, 0.9])

            with mid_left:
                st.markdown("""
                    <div style="margin-top:28px;">
                        <div style="font-family:'Orbitron'; font-size:2.2rem; font-weight:900; color:#00E5FF;">78%</div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#94A3B8;">Cognitive Capacity</div>
                        <div style="width:100%; height:6px; background:#0B172B; border-radius:4px; margin-top:8px; border:1px solid rgba(0,229,255,0.2);">
                            <div style="width:78%; height:100%; background:linear-gradient(90deg, #00E5FF, #E024A5); box-shadow:0 0 10px #00E5FF;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with mid_brain:
                # Stable Holographic Brain Wireframe via Plotly Scatter3D
                np.random.seed(42)
                phi = np.linspace(0, np.pi, 28)
                theta = np.linspace(0, 2 * np.pi, 28)
                x = np.outer(np.sin(phi), np.cos(theta)).flatten()
                y = np.outer(np.sin(phi), np.sin(theta)).flatten() * 0.8  # Ellipsoid like a brain
                z = np.outer(np.cos(phi), np.ones_like(theta)).flatten() * 0.7

                # Add noise for synaptic nodes
                x += np.random.normal(0, 0.04, len(x))
                y += np.random.normal(0, 0.04, len(y))
                z += np.random.normal(0, 0.04, len(z))

                fig_brain = go.Figure(data=[go.Scatter3d(
                    x=x, y=y, z=z,
                    mode='markers',
                    marker=dict(
                        size=2.8,
                        color=z,
                        colorscale=[[0, '#00E5FF'], [0.5, '#7C3AED'], [1, '#E024A5']],
                        opacity=0.85
                    ),
                    hoverinfo='none'
                )])
                fig_brain.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=180,
                    paper_bgcolor='rgba(0,0,0,0)',
                    scene=dict(
                        xaxis=dict(visible=False),
                        yaxis=dict(visible=False),
                        zaxis=dict(visible=False),
                        bgcolor='rgba(0,0,0,0)',
                        camera=dict(eye=dict(x=1.3, y=1.3, z=0.8))
                    )
                )
                st.plotly_chart(fig_brain, use_container_width=True, config={'displayModeBar': False})

            with mid_right:
                st.markdown("""
                    <div style="font-family:'JetBrains Mono'; font-size:0.75rem; text-align:right; margin-top:14px; display:flex; flex-direction:column; gap:8px;">
                        <div><span style="color:#64748B;">AI STATUS</span><br><span style="color:#10B981; font-weight:700;">ACTIVE</span></div>
                        <div><span style="color:#64748B;">MODEL</span><br><span style="color:#FFF; font-weight:700;">V6.4.1</span></div>
                        <div><span style="color:#64748B;">LATENCY</span><br><span style="color:#FFF; font-weight:700;">14ms</span></div>
                        <div><span style="color:#64748B;">THROUGHPUT</span><br><span style="color:#00E5FF; font-weight:700;">2.4M/s</span></div>
                    </div>
                """, unsafe_allow_html=True)

    with c_feed:
        st.markdown("""
            <div class="hud-box" style="height: 100%;">
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#00E5FF; letter-spacing:0.1em; margin-bottom:12px;">
                    ● LIVE INTELLIGENCE FEED
                </div>
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.1); border-radius:6px;">
                        <span>🛰️ Satellite signal intercepted</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">2 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.1); border-radius:6px;">
                        <span>📂 New data source validated</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">6 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.1); border-radius:6px;">
                        <span>⚠️ Anomalous traffic detected</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">12 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.1); border-radius:6px;">
                        <span>🔄 Model refinement complete</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">18 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.1); border-radius:6px;">
                        <span>🛡️ Threat pattern updated</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">23 min ago</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- ROW 2: 4 QUAD STAT PODS ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("TOTAL INTERCEPTS", f"{record_count:,}", "↑ 14%")
    with m2:
        st.metric("DATA SOURCES", "1,206", "↑ 8%")
    with m3:
        st.metric("THREATS DETECTED", "17", "-32%")
    with m4:
        st.metric("OPS ACTIVE", "4", "0%")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- ROW 3: GLOBAL SIGNAL MAP | SIGNAL INTENSITY | THREAT DISTRIBUTION ---
    b1, b2, b3 = st.columns([1.3, 1.2, 1], gap="medium")

    with b1:
        st.markdown("""
            <div class="hud-box">
                <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; margin-bottom:8px;">GLOBAL SIGNAL MAP</div>
        """, unsafe_allow_html=True)

        fig_map = go.Figure(go.Scattergeo(
            lon=[-74.0, 2.35, 139.69, -43.17, 37.61],
            lat=[40.71, 48.85, 35.68, -22.90, 55.75],
            text=["Active Intercept", "Relay Node", "High Threat", "Passive Node", "Monitoring Node"],
            mode='markers',
            marker=dict(
                size=[12, 9, 14, 9, 10],
                color=['#00E5FF', '#10B981', '#EF4444', '#E024A5', '#7C3AED'],
                line=dict(width=1, color='#FFFFFF')
            )
        ))
        fig_map.update_layout(
            geo=dict(
                bgcolor='rgba(0,0,0,0)',
                showland=True, landcolor='#0B1528',
                showocean=True, oceancolor='#040813',
                showcoastlines=True, coastlinecolor='rgba(0,229,255,0.2)',
                showframe=False
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=160,
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

        st.markdown("""
            <div style="display:flex; justify-content:space-around; font-family:'JetBrains Mono'; font-size:0.65rem; color:#64748B; margin-top:6px;">
                <span><b style="color:#00E5FF;">●</b> Active</span>
                <span><b style="color:#E024A5;">●</b> Intercept</span>
                <span><b style="color:#EF4444;">●</b> Threat</span>
                <span><b style="color:#10B981;">●</b> Relay</span>
            </div>
            </div>
        """, unsafe_allow_html=True)

    with b2:
        st.markdown("""
            <div class="hud-box">
                <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; margin-bottom:8px;">SIGNAL INTENSITY</div>
        """, unsafe_allow_html=True)

        t = np.linspace(0, 10, 80)
        s1 = np.sin(t) * 20 + 50
        s2 = np.cos(t * 1.5) * 15 + 40

        fig_wave = go.Figure()
        fig_wave.add_trace(go.Scatter(y=s1, mode='lines', line=dict(color='#00E5FF', width=2.5), hoverinfo='none'))
        fig_wave.add_trace(go.Scatter(y=s2, mode='lines', line=dict(color='#E024A5', width=2), hoverinfo='none'))
        fig_wave.update_layout(
            height=160,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        st.plotly_chart(fig_wave, use_container_width=True, config={'displayModeBar': False})

        st.markdown("""
            <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono'; font-size:0.65rem; color:#64748B; margin-top:6px;">
                <span>SPECTRUM: 2.4 - 5.8 GHz</span>
                <span style="color:#00E5FF;">PEAK AMPLITUDE: 94.2 dB</span>
            </div>
            </div>
        """, unsafe_allow_html=True)

    with b3:
        st.markdown("""
            <div class="hud-box">
                <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; margin-bottom:8px;">THREAT DISTRIBUTION</div>
        """, unsafe_allow_html=True)

        fig_donut = go.Figure(data=[go.Pie(
            labels=['Cyber', 'Comms', 'Physical', 'Financial', 'Other'],
            values=[41, 24, 18, 12, 5],
            hole=0.68,
            marker=dict(colors=['#00E5FF', '#7C3AED', '#E024A5', '#EF4444', '#64748B']),
            textinfo='none',
            hoverinfo='label+percent'
        )])
        fig_donut.update_layout(
            height=160,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            annotations=[dict(text='<b>17</b><br><span style="font-size:10px; color:#64748B;">THREATS</span>', x=0.5, y=0.5, font_size=15, font_color="#FFF", showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

        st.markdown("""
            <div style="display:flex; justify-content:space-around; font-family:'JetBrains Mono'; font-size:0.62rem; color:#94A3B8; margin-top:6px;">
                <span><b style="color:#00E5FF;">●</b> Cyber 41%</span>
                <span><b style="color:#7C3AED;">●</b> Comms 24%</span>
                <span><b style="color:#EF4444;">●</b> Fin 12%</span>
            </div>
            </div>
        """, unsafe_allow_html=True)


# ==================================================
# SCREEN: INTELLIGENCE & RESEARCH SYSTEM
# ==================================================
elif page == "INTELLIGENCE":
    st.markdown("<h2 style='font-family:Orbitron;'>// RESEARCH AUTOMATION & SIGNAL INTAKE</h2>", unsafe_allow_html=True)
    st.caption("Active integration bridge between Google Sheets and Groq LLM research agent.")

    if data_df.empty:
        st.warning("No records ingested from Google Sheets. Check configuration in Secrets.")
    else:
        st.dataframe(data_df.head(20), use_container_width=True, hide_index=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        record_idx = st.selectbox("Select Target Row to Synthesize", range(len(data_df)), format_func=lambda i: f"Row {i+2}: {str(data_df.iloc[i].get('Video Title', data_df.iloc[i].iloc[0]))[:80]}")

        if st.button("EXECUTE NEURAL GROQ ANALYSIS", type="primary"):
            with st.spinner("Analyzing GTA VI intelligence signals..."):
                try:
                    res = analyze_with_groq(data_df.iloc[record_idx].to_dict())
                    st.success("Target Intel Successfully Synthesized!")
                    st.json(res)
                except Exception as e:
                    st.error(f"Analysis error: {e}")


# ==================================================
# OTHER SCREENS (SYSTEM PLACEHOLDERS)
# ==================================================
else:
    st.markdown(f"<h2 style='font-family:Orbitron;'>// {page} SUBSYSTEM</h2>", unsafe_allow_html=True)
    st.info(f"Subsystem [{page}] active and operational. Telemetry nominal.")
