
import os
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# PREMIUM UI THEME
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #070B14;
    --panel: #0E1726;
    --line: #22334D;
    --muted: #91A4C2;
    --text: #EDF4FF;
    --purple: #7657FF;
    --pink: #ED4BBA;
    --green: #20D9A0;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: radial-gradient(
        ellipse at 65% 0%,
        #152043 0%,
        #070B14 48%
    );
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1220, #080D17);
    border-right: 1px solid #1D2A40;
}

.block-container {
    max-width: 1650px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.025em;
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #101C30, #0B1321);
    border: 1px solid #233651;
    padding: 16px;
    border-radius: 15px;
}

div[data-testid="stMetricLabel"] {
    color: #A6B8D2;
}

div[data-testid="stMetricValue"] {
    color: #F5F8FF;
}

.stButton > button {
    border-radius: 10px;
    border: 1px solid #31456A;
    background: #101D32;
    color: #EAF1FF;
    font-weight: 600;
    min-height: 2.5rem;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(100deg, #6948F5, #A447DF);
    border: 0;
    color: white;
}

.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stTextArea textarea {
    background: #0E1727 !important;
    border-color: #2A3B56 !important;
    border-radius: 10px !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #233651;
    border-radius: 12px;
    overflow: hidden;
}

.vp-hero {
    border: 1px solid #34365D;
    border-radius: 20px;
    padding: 28px;
    background: linear-gradient(
        110deg,
        #0C1223,
        #171335 60%,
        #471A53
    );
}

.vp-eyebrow {
    color: #B9A8FF;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.vp-hero p {
    color: #C0CCE0;
}

.vp-panel {
    background: linear-gradient(145deg, #0E1726, #0A111D);
    border: 1px solid #22334D;
    border-radius: 16px;
    padding: 18px;
}

.vp-small {
    color: #91A4C2;
    font-size: 0.8rem;
}

.vp-chip {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 8px;
    background: #1B2442;
    color: #B9A8FF;
    font-size: 0.72rem;
}

hr {
    border-color: #20304A;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SECRETS / CONNECTIONS
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

    if isinstance(raw, str):
        service_account = json.loads(raw)
    else:
        service_account = dict(raw)

    credentials = Credentials.from_service_account_info(
        service_account,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(credentials)

    return client.open_by_key(
        str(get_secret("GOOGLE_SHEET_ID"))
    )


@st.cache_data(ttl=30)
def load_worksheet(sheet_name):
    values = connect_google_sheets().worksheet(
        sheet_name
    ).get_all_values()

    if not values:
        return pd.DataFrame(), []

    headers = []
    seen = {}

    for index, header in enumerate(values[0]):
        header = (header or "").strip() or f"Column_{index + 1}"
        seen[header] = seen.get(header, 0) + 1

        if seen[header] > 1:
            header = f"{header}_{seen[header]}"

        headers.append(header)

    rows = [
        (row + [""] * max(0, len(headers) - len(row)))[:len(headers)]
        for row in values[1:]
    ]

    return pd.DataFrame(rows, columns=headers), headers


def find_column(columns, candidates):
    lookup = {
        str(column).strip().lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    for column in columns:
        if any(
            candidate.lower() in str(column).lower()
            for candidate in candidates
        ):
            return column

    return None


# --------------------------------------------------
# GROQ RESEARCH ANALYSIS
# --------------------------------------------------
def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    client = Groq(api_key=str(api_key))

    model = str(
        get_secret("GROQ_MODEL", "openai/gpt-oss-20b")
    )

    system_prompt = """
You are VicePlug Hub's GTA VI research editor.

Use only the supplied record. Do not invent facts, publication
dates, sources, or claim you watched the video.

Distinguish official information, reputable reporting, creator
commentary, and unverified claims.

Return valid JSON only with these keys:
relevance, priority_score, fact_status, summary,
why_it_matters, hook, commentary_draft, on_screen_text,
title, caption, hashtags, verification_needed,
rights_note, recommended_action.

priority_score must be an integer from 1 to 100.
commentary_draft should be suitable for a 20-35 second Short.
hashtags and verification_needed should be arrays.
Clearly identify claims that need independent verification.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        str(key): str(value)[:1500]
                        for key, value in record.items()
                        if str(value).strip()
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        temperature=0.2,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )

    return json.loads(
        response.choices[0].message.content or "{}"
    )


def save_analysis(worksheet, headers, row_number, result):
    output_columns = {
        "AI Relevance": result.get("relevance", ""),
        "AI Priority Score": result.get("priority_score", ""),
        "AI Fact Status": result.get("fact_status", ""),
        "AI Summary": result.get("summary", ""),
        "AI Why It Matters": result.get("why_it_matters", ""),
        "AI Hook": result.get("hook", ""),
        "AI Commentary Draft": result.get("commentary_draft", ""),
        "AI On-Screen Text": result.get("on_screen_text", ""),
        "AI Title": result.get("title", ""),
        "AI Caption": result.get("caption", ""),
        "AI Hashtags": " ".join(result.get("hashtags", []))
        if isinstance(result.get("hashtags"), list)
        else result.get("hashtags", ""),
        "AI Verification Needed": "; ".join(
            result.get("verification_needed", [])
        )
        if isinstance(result.get("verification_needed"), list)
        else result.get("verification_needed", ""),
        "AI Rights Note": result.get("rights_note", ""),
        "AI Recommended Action": result.get("recommended_action", ""),
        "AI Last Analyzed (UTC)": datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S"),
    }

    output_columns["Review Status"] = "Needs Review"

    new_headers = list(headers)

    for column in output_columns:
        if column not in new_headers:
            new_headers.append(column)

    if new_headers != list(headers):
        worksheet.update("1:1", [new_headers])

    old_row = worksheet.row_values(row_number)

    old_row = (
        old_row + [""] * max(0, len(new_headers) - len(old_row))
    )[:len(new_headers)]

    for column, value in output_columns.items():
        index = new_headers.index(column)

        # Don't reset an existing review decision unnecessarily.
        if column == "Review Status" and old_row[index].strip():
            continue

        old_row[index] = str(value)

    worksheet.update(
        f"A{row_number}",
        [old_row],
        value_input_option="USER_ENTERED",
    )


# --------------------------------------------------
# CONNECT AND LOAD DATA
# --------------------------------------------------
required = [
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_SHEET_ID",
    "GROQ_API_KEY",
]

missing = [
    name for name in required
    if not get_secret(name)
]

if missing:
    st.error("Missing Streamlit Secrets: " + ", ".join(missing))
    st.stop()

try:
    spreadsheet = connect_google_sheets()
    worksheet_names = [
        worksheet.title
        for worksheet in spreadsheet.worksheets()
    ]
except Exception as error:
    st.error("Could not connect to Google Sheets.")
    st.code(f"{type(error).__name__}: {error}")
    st.stop()


def find_worksheet(options):
    return next(
        (name for name in options if name in worksheet_names),
        None,
    )


tab_map = {
    "Video Discovery": find_worksheet(
        ["Video Discovery", "Video discovery"]
    ),
    "AI Analysis Clip Queue": find_worksheet(
        ["AI Analysis Clip Queue", "Clip Queue"]
    ),
    "New Trends": find_worksheet(["New Trends"]),
    "Performance": find_worksheet(["Performance"]),
    "Setup": find_worksheet(["Setup"]),
}

data = {}

for label, name in tab_map.items():
    if name:
        try:
            data[label] = load_worksheet(name)
        except Exception as error:
            st.warning(
                f"Could not load {name}: {type(error).__name__}"
            )
    else:
        data[label] = (pd.DataFrame(), [])

discovery, headers = data["Video Discovery"]
clip_queue, _ = data["AI Analysis Clip Queue"]
trends, _ = data["New Trends"]
performance, _ = data["Performance"]

title_col = find_column(
    discovery.columns,
    ["video title", "title", "headline", "topic", "name"],
) if not discovery.empty else None

url_col = find_column(
    discovery.columns,
    ["video url", "source url", "video link", "url", "link"],
) if not discovery.empty else None

status_col = find_column(
    discovery.columns,
    ["review status", "approval status", "status"],
) if not discovery.empty else None

score_col = find_column(
    discovery.columns,
    ["ai priority score", "priority score", "ai score", "score"],
) if not discovery.empty else None

analysis_col = find_column(
    discovery.columns,
    ["ai last analyzed", "ai summary", "ai hook"],
) if not discovery.empty else None

statuses = (
    discovery[status_col].astype(str).str.lower().str.strip()
    if status_col
    else pd.Series([], dtype=str)
)

pending_count = (
    int(statuses.isin(["", "pending", "needs review", "new", "to review"]).sum())
    if status_col else len(discovery)
)

approved_count = (
    int(statuses.isin(["approved", "approve"]).sum())
    if status_col else 0
)

analyzed_count = (
    int(discovery[analysis_col].astype(str).str.strip().ne("").sum())
    if analysis_col else 0
)


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.5rem">♛ <b>VicePlug '
        '<span style="color:#A18BFF">Hub</span></b></div>'
        '<div style="color:#91A4C2;font-size:.68rem;'
        'letter-spacing:.15em">GTA VI · CONTENT INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Video Discovery",
            "AI Analysis",
            "Clip Queue",
            "New Trends",
            "Performance",
            "Setup",
        ],
    )

    st.divider()
    st.markdown("**CONTENT WORKFLOW**")

    for number, name, description in [
        ("1", "Discover", "Find content opportunities"),
        ("2", "Analyze", "Rank stories and draft scripts"),
        ("3", "Create", "Edit and prepare clips"),
        ("4", "Publish", "Post after review"),
        ("5", "Grow", "Track results"),
    ]:
        st.markdown(
            f'<div style="padding:8px 0;border-bottom:1px solid #1C2A40">'
            f'<span style="color:#A998FF;font-weight:700">{number}</span> '
            f'<b>{name}</b><br><span style="color:#91A4C2;'
            f'font-size:.75rem;margin-left:18px">{description}</span></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    if st.button("↻ Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(
        "Review facts and confirm footage rights before publishing."
    )


# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------
if page == "Dashboard":

    st.markdown(
        """
        <div class="vp-hero">
            <div class="vp-eyebrow">YOUR CONTENT OPERATIONS CENTER</div>
            <h1>Welcome to VicePlug <span style="color:#A18BFF">Hub</span></h1>
            <p>
                Turn GTA VI hype into content opportunities.
                Discover stories, generate AI insights, and build a
                smarter short-form workflow.
            </p>
            <span style="color:#56E4C2">● Google Sheets connected</span>
            &nbsp;&nbsp;
            <span class="vp-chip">Groq AI enabled</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    columns = st.columns(5)

    metrics = [
        ("Total discovered", len(discovery), "Video Discovery records"),
        ("AI analyzed", analyzed_count, "AI fields populated"),
        ("Needs review", pending_count, "Awaiting your review"),
        ("Approved", approved_count, "Marked approved"),
        ("Trend records", len(trends), "New Trends worksheet"),
    ]

    for column, (label, value, help_text) in zip(columns, metrics):
        with column:
            st.metric(label, value, help_text)

    st.write("")

    left, middle, right = st.columns(
        [1.25, 1, 0.9],
        gap="medium",
    )

    with left:
        st.markdown("### 🔥 Discovery feed")
        st.caption("Latest records in your spreadsheet")

        if discovery.empty:
            st.info("No records found in Video Discovery.")
        else:
            for index, (_, record) in enumerate(
                discovery.head(7).iterrows()
            ):
                title = (
                    str(record.get(title_col, "Untitled"))
                    if title_col else f"Record {index + 1}"
                )

                score = (
                    str(record.get(score_col, "Unranked"))
                    if score_col else "Unranked"
                )

                status = (
                    str(record.get(status_col, "Needs review"))
                    if status_col else "Needs review"
                )

                st.markdown(
                    f'<div class="vp-panel" style="margin-bottom:9px">'
                    f'<span class="vp-chip">#{index + 1}</span> '
                    f'<b>{title[:100]}</b>'
                    f'<div class="vp-small" style="margin-top:9px">'
                    f'Priority: {score} &nbsp;·&nbsp; {status}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    with middle:
        st.markdown("### ◉ Content pipeline")

        pipeline = [
            ("Discovered", len(discovery), "#3BC4ED"),
            ("AI analyzed", analyzed_count, "#8368FF"),
            ("In clip queue", len(clip_queue), "#D451D7"),
            ("Approved", approved_count, "#20D9A0"),
        ]

        total = max(len(discovery), 1)

        for label, value, color in pipeline:
            percentage = min(int(value / total * 100), 100)

            st.markdown(
                f'<div style="margin:18px 0">'
                f'<div style="display:flex;justify-content:space-between">'
                f'<span>{label}</span><b>{value}</b></div>'
                f'<div style="height:7px;background:#1A2940;'
                f'border-radius:9px;margin-top:8px">'
                f'<div style="width:{percentage}%;height:7px;'
                f'background:{color};border-radius:9px"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        st.caption("Based on the rows and AI fields currently in Sheets.")

    with right:
        st.markdown("### ⚡ Quick actions")

        if st.button("🔎 Review discoveries", use_container_width=True):
            st.session_state["page_jump"] = "Video Discovery"
            st.rerun()

        if st.button("🧠 Open AI analysis", use_container_width=True):
            st.session_state["page_jump"] = "AI Analysis"
            st.rerun()

        if st.button("📋 Open clip queue", use_container_width=True):
            st.session_state["page_jump"] = "Clip Queue"
            st.rerun()

        if st.button("📈 View trends", use_container_width=True):
            st.session_state["page_jump"] = "New Trends"
            st.rerun()

        st.markdown(
            """
            <div class="vp-panel" style="margin-top:14px">
                <b>✦ Recommended next step</b>
                <p class="vp-small">
                    Analyze a promising story, verify the source, then
                    review the draft before editing.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 🗂️ Latest source records")

    if discovery.empty:
        st.info("Your discoveries will appear here.")
    else:
        st.dataframe(
            discovery.head(10),
            use_container_width=True,
            hide_index=True,
            height=300,
        )


# --------------------------------------------------
# DISCOVERY / ANALYSIS PAGES
# --------------------------------------------------
elif page in ["Video Discovery", "AI Analysis"]:

    st.title(
        "🔎 Video Discovery"
        if page == "Video Discovery"
        else "🧠 AI Analysis"
    )

    st.caption(
        "Search source records, then use Groq to rank the story "
        "and draft content. AI does not watch the source video."
    )

    if discovery.empty:
        st.warning("No records found in Video Discovery.")
    else:
        search = st.text_input(
            "Search records",
            placeholder="Search titles, creators, topics or notes",
        )

        filtered = discovery

        if search:
            mask = filtered.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    na=False,
                )
            ).any(axis=1)

            filtered = filtered[mask]

        st.dataframe(
            filtered.head(100),
            use_container_width=True,
            hide_index=True,
            height=320,
        )

        if title_col:
            labels = [
                f"Row {index + 2} · {str(record.get(title_col, ''))[:100]}"
                for index, (_, record) in enumerate(discovery.iterrows())
            ]

            chosen = st.selectbox("Select a record", labels)
            row_index = labels.index(chosen)
            record = discovery.iloc[row_index].to_dict()

            if url_col and str(record.get(url_col, "")).strip():
                st.markdown(
                    f"[↗ Open source]({record[url_col]})"
                )

            with st.expander("View source details"):
                st.json({
                    str(key): str(value)
                    for key, value in record.items()
                    if str(value).strip()
                })

            if st.button(
                "✨ Analyze with Groq and save results",
                type="primary",
            ):
                try:
                    with st.spinner(
                        "Ranking the opportunity and drafting content..."
                    ):
                        result = analyze_with_groq(record)

                        save_analysis(
                            spreadsheet.worksheet(
                                tab_map["Video Discovery"]
                            ),
                            headers,
                            row_index + 2,
                            result,
                        )

                    st.session_state["latest_result"] = result
                    st.cache_data.clear()
                    st.success("Analysis saved to Video Discovery.")

                except Exception as error:
                    st.error("AI analysis failed.")
                    st.code(f"{type(error).__name__}: {error}")

    result = st.session_state.get("latest_result")

    if result:
        st.divider()

        a, b, c = st.columns(3)

        a.metric("Priority score", result.get("priority_score", "—"))
        b.metric("Relevance", result.get("relevance", "—"))
        c.metric("Evidence type", result.get("fact_status", "—"))

        for label, key in [
            ("Story summary", "summary"),
            ("Why it matters", "why_it_matters"),
            ("Hook", "hook"),
            ("Commentary draft", "commentary_draft"),
            ("On-screen text", "on_screen_text"),
            ("Title", "title"),
            ("Caption", "caption"),
        ]:
            st.subheader(label)
            st.write(result.get(key, ""))

        hashtags = result.get("hashtags", [])

        st.write(
            "**Hashtags:**",
            " ".join(hashtags)
            if isinstance(hashtags, list)
            else hashtags,
        )

        st.write(
            "**Verify before posting:**",
            result.get("verification_needed", []),
        )

        st.write(
            "**Footage rights:**",
            result.get("rights_note", ""),
        )


# --------------------------------------------------
# CLIP QUEUE
# --------------------------------------------------
elif page == "Clip Queue":

    st.title("📋 Clip Queue")
    st.caption("Records currently stored in your clip queue worksheet.")

    if clip_queue.empty:
        st.info(
            "The queue is empty or its worksheet was not found. "
            "Automatic transfer from AI analysis to this queue "
            "has not been implemented yet."
        )
    else:
        st.dataframe(
            clip_queue,
            use_container_width=True,
            hide_index=True,
            height=550,
        )


# --------------------------------------------------
# NEW TRENDS
# --------------------------------------------------
elif page == "New Trends":

    st.title("📈 New Trends")
    st.caption("Current trend records from Google Sheets.")

    if trends.empty:
        st.info("No trend records found yet.")
    else:
        st.dataframe(
            trends,
            use_container_width=True,
            hide_index=True,
            height=550,
        )


# --------------------------------------------------
# PERFORMANCE
# --------------------------------------------------
elif page == "Performance":

    st.title("📊 Performance")
    st.caption("Performance data currently stored in Google Sheets.")

    if performance.empty:
        st.info(
            "No performance records found yet. "
            "Posting analytics can be connected later."
        )
    else:
        st.dataframe(
            performance,
            use_container_width=True,
            hide_index=True,
            height=550,
        )


# --------------------------------------------------
# SETUP
# --------------------------------------------------
elif page == "Setup":

    st.title("⚙️ Setup & integrations")

    left, right = st.columns(2)

    with left:
        st.markdown("### Connected services")
        st.success("Google Sheets connected")

        st.write(
            "Groq API key:",
            "Configured" if get_secret("GROQ_API_KEY") else "Missing",
        )

        st.write(
            "Groq model:",
            get_secret("GROQ_MODEL", "openai/gpt-oss-20b"),
        )

    with right:
        st.markdown("### Detected worksheets")

        for name in worksheet_names:
            st.write("🟢 " + name)

    st.info(
        "Keep API keys in Streamlit Secrets. Automated news discovery, "
        "automatic queue routing, and publishing analytics are "
        "separate integrations and are not enabled by this UI redesign."
    )
