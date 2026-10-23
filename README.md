# VicePlug Hub Dashboard

A starter web dashboard for the existing VicePlug Hub Google Sheet and Groq API. It is designed for GTA VI research and script drafting. It does **not** inspect video footage or automatically publish to YouTube/TikTok.

## Files
- `app.py` — Streamlit dashboard
- `requirements.txt` — cloud dependencies
- `secrets_template.toml` — configuration template; replace placeholders in Streamlit settings. Do not commit real secrets.

## 1. Prepare GitHub
1. Create a GitHub repository named `viceplug-hub-dashboard`.
2. Upload `app.py`, `requirements.txt`, and optionally this README.
3. Do **not** upload `.env`, `service-account.json`, API keys, or real secrets.
4. A private repository is preferable for your code. Check the current Streamlit app privacy options before deploying.

## 2. Deploy free on Streamlit Community Cloud
1. Open https://share.streamlit.io/ and sign in with GitHub.
2. Choose **Create app**.
3. Select your repository, branch `main`, and entrypoint `app.py`.
4. Open **Advanced settings → Secrets** and paste configured secrets (below).
5. Deploy. Streamlit assigns a `*.streamlit.app` URL.

## 3. Configure secrets
Use `secrets_template.toml` as a guide. Add the Groq key, Google Sheet ID, worksheet tab name, and full service-account JSON in the Streamlit app's **Settings → Secrets**. The multiline service-account value should use TOML triple-double-quotes (`""" ... """`). Never put real keys in GitHub or share them in chat.

`GOOGLE_SHEET_ID` is the text between `/d/` and `/edit` in the spreadsheet URL. `GOOGLE_WORKSHEET_NAME` is the tab name at the bottom of the spreadsheet. If omitted, the app uses the first tab. Share the sheet with the service-account email as an Editor.

## 4. Test safely
1. Deploy and check that the dashboard says the sheet is connected.
2. Select one existing research row.
3. Click **Analyze with Groq and save to Sheet**.
4. Check that new `AI ...` columns were added and populated.
5. The app sets `Review Status` to `Needs Review` only if that field is blank.

## Current scope
This starter dashboard reads existing rows from Google Sheets and lets you run Groq analysis on a selected record. It does not yet replace the existing Apps Script discovery trigger or implement a full web news crawler. Keep the existing research workflow active. Once the dashboard connects, the next integration step is to adapt discovery so it finds GTA VI news, stores source URLs and dates, deduplicates stories, and sends them to this review queue.

## Troubleshooting
- **Missing secrets**: check spelling in Streamlit app Settings → Secrets.
- **Google permission error**: share the sheet with the service account's `client_email` as Editor.
- **Worksheet not found**: use the exact tab name or remove `GOOGLE_WORKSHEET_NAME` to use the first tab.
- **Groq model error / 404**: check currently available model IDs at https://console.groq.com/docs/models and update `GROQ_MODEL`.
- **Groq 429**: retry later or reduce request frequency.
