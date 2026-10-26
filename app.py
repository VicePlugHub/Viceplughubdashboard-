            pipeline_sheet_name = pipeline_ws.title if pipeline_ws is not None else str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))

        if pipeline_df.empty:
            show_missing_data(pipeline_message)
        else:
            s_col = status_column(pipeline_df)
            if not s_col:
                st.warning(f"No Review Status / Status column was detected in {pipeline_sheet_name}. Add a status column to enable stage tracking.")
                st.dataframe(clean_display_df(pipeline_df), use_container_width=True, hide_index=True)
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
                st.dataframe(clean_display_df(shown, 12), use_container_width=True, hide_index=True, height=350)
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
            st.caption("This screen currently reads the configured research worksheet. Status edits in Content Pipeline / Review Queue are written back when a supported status column exists.")
            st.dataframe(clean_display_df(df, 14), use_container_width=True, hide_index=True, height=470)
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
