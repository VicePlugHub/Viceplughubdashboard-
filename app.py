import json, os
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

st.set_page_config(page_title="VicePlug Hub | Operations", page_icon="🎬", layout="wide")
st.markdown("""
<style>
.stApp{background:#0b0d12}[data-testid="stSidebar"]{background:#10141d}
.block-container{padding-top:1.5rem;max-width:1600px}
.vphero{background:linear-gradient(120deg,#171e2b,#11151e);border:1px solid #293246;padding:24px;border-radius:18px}
.vpeye{color:#a6afc2;text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;font-weight:700}
.vpsub{color:#aab3c3}
.vpmetric{background:#141a25;border:1px solid #252e3f;border-radius:14px;padding:16px;min-height:100px}
.vplabel{color:#a6afc2;font-size:.8rem}.vpvalue{font-size:1.8rem;font-weight:750;margin-top:5px}
.vpnote{background:#121925;border:1px solid #28354a;border-radius:12px;padding:14px}
</style>""", unsafe_allow_html=True)

def secret(k, default=None):
    try:
        if k in st.secrets: return st.secrets[k]
    except Exception: pass
    return os.getenv(k, default)

@st.cache_resource
def spreadsheet():
    raw=secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    info=json.loads(raw) if isinstance(raw,str) else dict(raw)
    creds=Credentials.from_service_account_info(info,scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key(str(secret("GOOGLE_SHEET_ID")))

@st.cache_data(ttl=30)
def load_tab(name):
    vals=spreadsheet().worksheet(name).get_all_values()
    if not vals: return pd.DataFrame(), []
    headers=[]; seen={}
    for i,h in enumerate(vals[0]):
        h=(h or "").strip() or f"Column_{i+1}"; seen[h]=seen.get(h,0)+1
        headers.append(h if seen[h]==1 else f"{h}_{seen[h]}")
    rows=[(r+[""]*max(0,len(headers)-len(r)))[:len(headers)] for r in vals[1:]]
    return pd.DataFrame(rows,columns=headers),headers

def find_col(cols, names):
    low={str(c).strip().lower():c for c in cols}
    for n in names:
        if n.lower() in low: return low[n.lower()]
    for c in cols:
        if any(n.lower() in str(c).lower() for n in names): return c
    return None

def metric(col,label,value,sub):
    with col: st.markdown(f'<div class="vpmetric"><div class="vplabel">{label}</div><div class="vpvalue">{value}</div><div class="vplabel">{sub}</div></div>',unsafe_allow_html=True)

def analyze(record):
    client=Groq(api_key=str(secret("GROQ_API_KEY")))
    model=str(secret("GROQ_MODEL","openai/gpt-oss-20b"))
    system="""You are VicePlug Hub's GTA VI research editor. Use only supplied fields. Do not invent facts or claim to have watched/verified a source. Distinguish official information, reputable reporting, creator commentary and unverified claims. Return JSON only: relevance (High/Medium/Low), priority_score (1-100), fact_status, summary, why_it_matters, hook, commentary_draft (20-35 sec), on_screen_text, title, caption, hashtags (array), verification_needed (array), rights_note, recommended_action."""
    response=client.chat.completions.create(model=model,messages=[{"role":"system","content":system},{"role":"user","content":json.dumps({str(k):str(v)[:1500] for k,v in record.items() if str(v).strip()},ensure_ascii=False)}],temperature=.2,max_tokens=1200,response_format={"type":"json_object"})
    return json.loads(response.choices[0].message.content or "{}")

def save_analysis(ws, headers, row_num, r):
    desired=["AI Relevance","AI Priority Score","AI Fact Status","AI Summary","AI Why It Matters","AI Hook","AI Commentary Draft","AI On-Screen Text","AI Title","AI Caption","AI Hashtags","AI Verification Needed","AI Rights Note","AI Recommended Action","AI Last Analyzed (UTC)","Review Status"]
    new=list(headers)
    for h in desired:
        if h not in new: new.append(h)
    if new!=list(headers): ws.update("1:1",[new])
    old=ws.row_values(row_num); old=(old+[""]*max(0,len(new)-len(old)))[:len(new)]
    values={"AI Relevance":r.get("relevance",""),"AI Priority Score":r.get("priority_score",""),"AI Fact Status":r.get("fact_status",""),"AI Summary":r.get("summary",""),"AI Why It Matters":r.get("why_it_matters",""),"AI Hook":r.get("hook",""),"AI Commentary Draft":r.get("commentary_draft",""),"AI On-Screen Text":r.get("on_screen_text",""),"AI Title":r.get("title",""),"AI Caption":r.get("caption",""),"AI Hashtags":" ".join(r.get("hashtags",[])) if isinstance(r.get("hashtags"),list) else r.get("hashtags",""),"AI Verification Needed":"; ".join(r.get("verification_needed",[])) if isinstance(r.get("verification_needed"),list) else r.get("verification_needed",""),"AI Rights Note":r.get("rights_note",""),"AI Recommended Action":r.get("recommended_action",""),"AI Last Analyzed (UTC)":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
    for k,v in values.items(): old[new.index(k)]=str(v)
    si=new.index("Review Status")
    if not old[si].strip(): old[si]="Needs Review"
    ws.update(f"A{row_num}",[old],value_input_option="USER_ENTERED")

st.sidebar.markdown("## 🎬 VicePlug Hub")
st.sidebar.caption("Creator intelligence · Research · Editorial")
page=st.sidebar.radio("WORKSPACE",["Overview","Video Discovery","AI Analysis","Clip Queue","New Trends","Performance","Settings"])
st.sidebar.divider()
st.sidebar.write("**Workflow**")
st.sidebar.caption("Discover → Evaluate → Draft → Approve → Edit → Publish")
st.sidebar.caption("Research mode: GTA VI news. Local video analysis is disabled.")
if st.sidebar.button("↻ Refresh data",use_container_width=True): st.cache_data.clear(); st.rerun()
st.sidebar.caption("Verify facts and footage rights before publishing.")

missing=[k for k in ["GROQ_API_KEY","GOOGLE_SERVICE_ACCOUNT_JSON","GOOGLE_SHEET_ID"] if not secret(k)]
if missing: st.error("Missing Streamlit Secrets: "+", ".join(missing)); st.stop()
try:
    ss=spreadsheet(); tabs=[w.title for w in ss.worksheets()]
except Exception as e:
    st.error("Google Sheets connection failed."); st.code(f"{type(e).__name__}: {e}"); st.stop()

def resolve(candidates): return next((x for x in candidates if x in tabs),None)
tabmap={"Video Discovery":resolve(["Video Discovery","Video discovery"]),"AI Analysis Clip Queue":resolve(["AI Analysis Clip Queue","Clip Queue"]),"New Trends":resolve(["New Trends"]),"Performance":resolve(["Performance"]),"Setup":resolve(["Setup"])}
data={}
for label,name in tabmap.items():
    if name:
        try: data[label]=load_tab(name)
        except Exception as e: st.warning(f"Couldn't load {name}: {type(e).__name__}: {e}")
    else: data[label]=(pd.DataFrame(),[])
discovery,dh=data.get("Video Discovery",(pd.DataFrame(),[]))
queue,qh=data.get("AI Analysis Clip Queue",(pd.DataFrame(),[]))
trends,th=data.get("New Trends",(pd.DataFrame(),[]))
perf,ph=data.get("Performance",(pd.DataFrame(),[]))
titlecol=find_col(discovery.columns,["video title","title","headline","topic","name"]) if not discovery.empty else None
urlcol=find_col(discovery.columns,["video url","source url","video link","url","link"]) if not discovery.empty else None
statuscol=find_col(discovery.columns,["review status","approval status","status"]) if not discovery.empty else None
scorecol=find_col(discovery.columns,["ai priority score","priority score","ai score","score"]) if not discovery.empty else None
status=discovery[statuscol].astype(str).str.lower().str.strip() if statuscol else pd.Series([],dtype=str)
needs=int(status.isin(["","needs review","pending","new","to review"]).sum()) if statuscol else len(discovery)
approved=int(status.isin(["approved","approve"]).sum()) if statuscol else 0
analyzed=int(discovery[find_col(discovery.columns,["ai last analyzed","ai summary","ai hook"])].astype(str).str.strip().ne("").sum()) if not discovery.empty and find_col(discovery.columns,["ai last analyzed","ai summary","ai hook"]) else 0

if page=="Overview":
    st.markdown('<div class="vphero"><div class="vpeye">OPERATIONS CENTER</div><h1>VicePlug Hub</h1><div class="vpsub">Turn GTA VI developments into ranked, review-ready short-form content opportunities.</div></div>',unsafe_allow_html=True)
    st.write("")
    cols=st.columns(5)
    for c,l,v,s in zip(cols,["Discovered","Needs review","Approved","AI analyzed","Worksheets"],[len(discovery),needs,approved,analyzed,len(tabs)],["Video Discovery","Awaiting your review","Approved records","Detected AI fields","Available in Google Sheets"]): metric(c,l,v,s)
    st.subheader("Priority workspace")
    left,right=st.columns([1.5,1])
    with left:
        st.markdown("#### Recent discoveries")
        if discovery.empty: st.info("No rows found in Video Discovery.")
        else:
            show=[c for c in [titlecol,urlcol,scorecol,statuscol] if c]
            st.dataframe(discovery[show or list(discovery.columns[:5])].head(12),use_container_width=True,hide_index=True)
    with right:
        st.markdown("#### Worksheet connections")
        for n in ["Video Discovery","AI Analysis Clip Queue","New Trends","Performance","Setup"]:
            st.write(("🟢 " if tabmap[n] else "⚪ ")+n+("" if tabmap[n] else " — not found"))
        st.markdown('<div class="vpnote">Next: select a discovery record, run Groq analysis, check sources and rights, then edit manually.</div>',unsafe_allow_html=True)
    st.subheader("Content pipeline")
    cs=st.columns(5)
    for c,num,name,desc in zip(cs,["01","02","03","04","05"],["Discover","Evaluate","Draft","Approve","Publish"],["Collect sources","Rank story","Write hook/script","Fact-check","Edit and post"]):
        with c: st.markdown(f'<div class="vpmetric"><div class="vplabel">{num}</div><div class="vpvalue" style="font-size:1.15rem">{name}</div><div class="vplabel">{desc}</div></div>',unsafe_allow_html=True)

elif page in ["Video Discovery","AI Analysis"]:
    st.title("🔎 Video Discovery" if page=="Video Discovery" else "🧠 AI Analysis")
    st.caption("Groq evaluates the fields already in your sheet. It does not watch footage or independently verify claims.")
    if discovery.empty: st.warning("No records found in the Video Discovery tab.")
    else:
        search=st.text_input("Search records",placeholder="Title, topic, creator or note")
        view=discovery
        if search: view=view[view.astype(str).apply(lambda x:x.str.contains(search,case=False,na=False)).any(axis=1)]
        st.dataframe(view.head(100),use_container_width=True,hide_index=True,height=340)
        tc=find_col(discovery.columns,["video title","title","headline","topic","name"])
        if tc:
            labels=[f"Row {i+2} · {str(r.get(tc,''))[:110]}" for i,(_,r) in enumerate(discovery.iterrows())]
            chosen=st.selectbox("Select a record",labels)
            idx=labels.index(chosen); record=discovery.iloc[idx].to_dict()
            if urlcol and str(record.get(urlcol,"")).strip(): st.markdown(f"[Open source]({record[urlcol]})")
            with st.expander("View source fields"): st.json({str(k):str(v) for k,v in record.items() if str(v).strip()})
            if st.button("✨ Analyze with Groq and save to Video Discovery",type="primary"):
                try:
                    with st.spinner("Evaluating the record and drafting content..."):
                        result=analyze(record)
                        save_analysis(ss.worksheet(tabmap["Video Discovery"]),dh,idx+2,result)
                    st.session_state["latest_result"]=result; st.cache_data.clear(); st.success("Analysis saved.")
                except Exception as e: st.error("Analysis failed."); st.code(f"{type(e).__name__}: {e}")
    result=st.session_state.get("latest_result")
    if result:
        st.divider(); a,b,c=st.columns(3)
        a.metric("Priority",result.get("priority_score","—")); b.metric("Relevance",result.get("relevance","—")); c.metric("Evidence class",result.get("fact_status","—"))
        for label,key in [("Summary","summary"),("Why it matters","why_it_matters"),("Hook","hook"),("Commentary draft","commentary_draft"),("Title","title"),("Caption","caption")]:
            st.markdown("#### "+label); st.write(result.get(key,""))
        st.write("**Hashtags:**"," ".join(result.get("hashtags",[])) if isinstance(result.get("hashtags"),list) else result.get("hashtags",""))
        st.write("**Verification needed:**",result.get("verification_needed",[]))
        st.write("**Rights note:**",result.get("rights_note",""))

elif page=="Clip Queue":
    st.title("📋 AI Analysis Clip Queue")
    st.caption("Current rows from your existing queue tab.")
    if queue.empty: st.info("The queue is empty or its tab was not found. This version currently saves analysis into Video Discovery; automatic queue routing is a next step.")
    else: st.dataframe(queue,use_container_width=True,hide_index=True,height=520)

elif page=="New Trends":
    st.title("📈 New Trends")
    st.caption("Trend records already stored in your Google Sheet.")
    if trends.empty: st.info("No trend rows found yet. Automated trend discovery is a future integration.")
    else: st.dataframe(trends,use_container_width=True,hide_index=True,height=520)

elif page=="Performance":
    st.title("📊 Performance")
    st.caption("Performance data currently recorded in your sheet.")
    if perf.empty: st.info("No performance rows found yet. Posting metrics can be connected later.")
    else: st.dataframe(perf,use_container_width=True,hide_index=True,height=520)

elif page=="Settings":
    st.title("⚙️ Settings & connections")
    st.success("Google Sheets authenticated")
    st.write("Groq API key configured:", "Yes" if secret("GROQ_API_KEY") else "No")
    st.write("Groq model:",secret("GROQ_MODEL","openai/gpt-oss-20b"))
    st.subheader("Detected worksheets")
    for t in tabs: st.write("✅ "+t)
    st.subheader("Detected columns")
    if not discovery.empty: st.write("**Video Discovery:**",", ".join(map(str,discovery.columns)))
    if not queue.empty: st.write("**AI Analysis Clip Queue:**",", ".join(map(str,queue.columns)))
    st.caption("Credentials are not displayed. Keep all secrets in Streamlit app settings.")
