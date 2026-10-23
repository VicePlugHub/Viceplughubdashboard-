import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

st.set_page_config(
    page_title="VicePlug Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: #0b0d12; }
    [data-testid="stSidebar"] { background: #11141c; }
    .vp-muted { color: #9ca3af; font-size: 0.9rem; }
    .vp-card {
        background: #141923; border: 1px solid #252b38;
        border-radius: 14px; padding: 16px 18px; min-height: 100px;
    }
    .vp-label { color: #9ca3af; font-size: 0.85rem; }
    .vp-value { font-size: 1.65rem; font-weight: 700; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


def secret(name, default=None):
    """Read Streamlit Cloud secrets first, then local environment variables."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def get_config():
    required = ["GROQ_API_KEY", "GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_SHEET_ID"]
    missing = [key for key in required if not secret(key)]
    return missing


@st.cache_resource
def connect_sheet():
    raw = secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON in app secrets.")
    if isinstance(raw, str):
        service_info = json.loads(raw)
    else:
        service_info = dict(raw)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(service_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(str(secret("GOOGLE_SHEET_ID")))
    tab_name = secret("GOOGLE_WORKSHEET_NAME", "")
    worksheet = spreadsheet.worksheet(str(tab_name)) if tab_name else spreadsheet.sheet1
    return worksheet


def read_records(worksheet):
    values = worksheet.get_all_values()
    if not values:
        return pd.DataFrame(), []
    headers = values[0]
    # Avoid pandas errors from duplicate or blank headers.
    clean_headers = []
    counts = {}
    for i, header in enumerate(headers):
        name = (header or "").strip() or f"Column_{i+1}"
        counts[name] = counts.get(name, 0) + 1
        if counts[name] > 1:
            name = f"{name}_{counts[name]}"
        clean_headers.append(name)
    rows = values[1:]
    if not rows:
        return pd.DataFrame(columns=clean_headers), clean_headers
    width = len(clean_headers)
    normalized = [(row + [""] * (width - len(row)))[:width] for row in rows]
    return pd.DataFrame(normalized, columns=clean_headers), clean_headers


def find_column(columns, candidates):
    lookup = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    for c in columns:
        lowered = str(c).strip().lower()
        if any(candidate.lower() in lowered for candidate in candidates):
            return c
    return None


def ensure_columns(worksheet, headers, desired):
    changed = False
    for column in desired:
        if column not in headers:
            headers.append(column)
            changed = True
    if changed:
        worksheet.update("1:1", [headers])
    return headers


def analyze_with_groq(row_dict):
    api_key = secret("GROQ_API_KEY")
    model = secret("GROQ_MODEL", "openai/gpt-oss-20b")
    client = Groq(api_key=str(api_key))

    # Send only a compact set of row fields to the model.
    content = {str(k): str(v)[:1800] for k, v in row_dict.items() if str(v).strip()}
    system_prompt = """
You are the editorial research assistant for VicePlug Hub, a GTA VI short-form content brand.
Use only the evidence provided in the row. Do not invent facts, release details, gameplay,
quotes, dates, or sources. Clearly label uncertainty and rumors. If the row is not about GTA VI,
say so. Do not claim you watched a video or verified a source. Return valid JSON only with:
relevance (High/Medium/Low), priority_score (integer 1-100), fact_status
(Official/Reputable reporting/Creator commentary/Unverified), summary, why_it_matters,
hook, commentary_draft (about 20-35 seconds), on_screen_text, title, caption,
hashtags (array of strings), verification_needed (array of strings), rights_note.
"""
    response = client.chat.completions.create(
        model=str(model),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Evaluate this research record:\n" + json.dumps(content, ensure_ascii=False)},
        ],
        temperature=0.2,
        max_tokens=1100,
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content or "{}"
    return json.loads(text)


def write_analysis(worksheet, headers, sheet_row, analysis):
    desired = [
        "AI Relevance", "AI Priority Score", "AI Fact Status", "AI Summary",
        "AI Why It Matters", "AI Hook", "AI Commentary Draft", "AI On-Screen Text",
        "AI Title", "AI Caption", "AI Hashtags", "AI Verification Needed",
        "AI Rights Note", "AI Last Analyzed (UTC)", "Review Status",
    ]
    headers = ensure_columns(worksheet, list(headers), desired)
    # Existing sheet row number includes header row.
    current = worksheet.row_values(sheet_row)
    current = (current + [""] * (len(headers) - len(current)))[:len(headers)]
    values = {
        "AI Relevance": analysis.get("relevance", ""),
        "AI Priority Score": analysis.get("priority_score", ""),
        "AI Fact Status": analysis.get("fact_status", ""),
        "AI Summary": analysis.get("summary", ""),
        "AI Why It Matters": analysis.get("why_it_matters", ""),
        "AI Hook": analysis.get("hook", ""),
        "AI Commentary Draft": analysis.get("commentary_draft", ""),
        "AI On-Screen Text": analysis.get("on_screen_text", ""),
        "AI Title": analysis.get("title", ""),
        "AI Caption": analysis.get("caption", ""),
        "AI Hashtags": " ".join(analysis.get("hashtags", [])) if isinstance(analysis.get("hashtags"), list) else analysis.get("hashtags", ""),
        "AI Verification Needed": "; ".join(analysis.get("verification_needed", [])) if isinstance(analysis.get("verification_needed"), list) else analysis.get("verification_needed", ""),
        "AI Rights Note": analysis.get("rights_note", ""),
        "AI Last Analyzed (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    # Only set a default review status if the cell is currently blank.
    for header, value in values.items():
        current[headers.index(header)] = str(value)
    status_idx = headers.index("Review Status")
    if not current[status_idx].strip():
        current[status_idx] = "Needs Review"
    worksheet.update(f"A{sheet_row}", [current], value_input_option="USER_ENTERED")
    return headers


st.title("🎬 VicePlug Hub")
st.caption("GTA VI research desk · AI-assisted, human-approved")

missing = get_config()
if missing:
    st.warning("The dashboard needs its hosting secrets configured before it can connect.")
    st.markdown("Missing: " + ", ".join(f"`{x}`" for x in missing))
    st.markdown("""
    Open the app's **Settings → Secrets** in Streamlit Community Cloud and add the values
    from `secrets_template.toml`. Never put API keys or the service-account JSON in your GitHub code.
    """)
    st.stop()

with st.sidebar:
    st.header("Control panel")
    st.markdown("**Mode:** Research and script drafting")
    st.caption("Local video analysis is disabled in this dashboard.")
    if st.button("Refresh sheet data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption("Before publishing, verify the source and confirm that you have the necessary rights or permission to use any footage.")

try:
    worksheet = connect_sheet()
    df, headers = read_records(worksheet)
except Exception as exc:
    st.error("Could not connect to Google Sheets.")
    st.code(f"{type(exc).__name__}: {exc}")
    st.info("Check the Sheet ID, worksheet name, service-account JSON, and that the sheet is shared with the service-account email.")
    st.stop()

if df.empty:
    st.info("Your Google Sheet is connected, but it has no research rows yet. Run your existing research collection workflow, then refresh.")
    st.stop()

url_col = find_column(df.columns, ["video url", "url", "link", "video link", "source url"])
title_col = find_column(df.columns, ["video title", "title", "topic", "headline", "name"])
status_col = find_column(df.columns, ["review status", "approval status", "status"])
score_col = find_column(df.columns, ["ai priority score", "priority score", "score"])

total = len(df)
pending = 0
if status_col:
    pending = int(df[status_col].astype(str).str.lower().isin(["", "needs review", "pending", "new"]).sum())

c1, c2, c3, c4 = st.columns(4)
for col, label, value in [
    (c1, "Research records", total),
    (c2, "Needs review", pending),
    (c3, "AI-analyzed", int(df["AI Last Analyzed (UTC)"].astype(str).str.strip().ne("").sum()) if "AI Last Analyzed (UTC)" in df.columns else 0),
    (c4, "Sheet status", "Connected"),
]:
    with col:
        st.markdown(f'<div class="vp-card"><div class="vp-label">{label}</div><div class="vp-value">{value}</div></div>', unsafe_allow_html=True)

st.divider()
left, right = st.columns([1.35, 1])

with left:
    st.subheader("Research queue")
    search_text = st.text_input("Search titles, sources, or notes", placeholder="Search GTA VI news, creator, topic...")
    filter_status = st.selectbox("Review filter", ["All records", "Needs review", "Approved", "Rejected"])
    filtered = df.copy()
    if search_text:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(search_text, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]
    if status_col and filter_status != "All records":
        target = filter_status.lower()
        if filter_status == "Needs review":
            filtered = filtered[filtered[status_col].astype(str).str.lower().isin(["", "needs review", "pending", "new"])]
        else:
            filtered = filtered[filtered[status_col].astype(str).str.lower() == target]
    display_cols = [c for c in [title_col, url_col, score_col, status_col] if c]
    if not display_cols:
        display_cols = list(filtered.columns[:5])
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True, height=360)

with right:
    st.subheader("Analyze a record")
    if title_col:
        labels = []
        for idx, row in df.iterrows():
            title = str(row.get(title_col, "")).strip() or "(untitled record)"
            labels.append(f"Row {idx + 2}: {title[:100]}")
    else:
        labels = [f"Row {idx + 2}" for idx in df.index]

    selected_label = st.selectbox("Choose a row", labels)
    selected_index = labels.index(selected_label)
    selected_row = df.iloc[selected_index]
    st.markdown(f"**{str(selected_row.get(title_col, 'Selected record')) if title_col else 'Selected record'}**")
    if url_col and str(selected_row.get(url_col, "")).strip():
        st.markdown(f"[Open source]({selected_row.get(url_col)})")
    with st.expander("View source record"):
        st.json({str(k): str(v) for k, v in selected_row.to_dict().items() if str(v).strip()})

    if st.button("✨ Analyze with Groq and save to Sheet", type="primary", use_container_width=True):
        try:
            with st.spinner("Analyzing the selected record..."):
                result = analyze_with_groq(selected_row.to_dict())
                sheet_row = selected_index + 2
                write_analysis(worksheet, headers, sheet_row, result)
            st.success("Analysis saved to Google Sheets.")
            st.session_state["last_analysis"] = result
        except Exception as exc:
            st.error("Analysis failed. Check the model name, Groq limits, and Google Sheets permissions.")
            st.code(f"{type(exc).__name__}: {exc}")

if "last_analysis" in st.session_state:
    st.divider()
    st.subheader("Latest AI draft")
    result = st.session_state["last_analysis"]
    st.markdown(f"**Priority:** {result.get('priority_score', '—')}/100 · **Relevance:** {result.get('relevance', '—')} · **Classification:** {result.get('fact_status', '—')}")
    st.markdown(f"**Hook**\n\n{result.get('hook', '')}")
    st.markdown(f"**Commentary draft**\n\n{result.get('commentary_draft', '')}")
    st.markdown(f"**Title**\n\n{result.get('title', '')}")
    st.markdown(f"**Caption**\n\n{result.get('caption', '')}")
    st.markdown(f"**Hashtags**\n\n{' '.join(result.get('hashtags', [])) if isinstance(result.get('hashtags'), list) else result.get('hashtags', '')}")
    with st.expander("Verification and rights checklist"):
        st.write("**Needs verification:**", result.get("verification_needed", []))
        st.write("**Rights note:**", result.get("rights_note", ""))
