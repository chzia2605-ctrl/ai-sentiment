# Minimal AI Sentiment SPA (Flask + Gemini)

A tiny single-page application: HTML frontend + Python Flask backend that performs sentiment analysis. It can call Google Gemini (Vertex AI) if configured, or use a simple fallback analyzer.

## Quick start (fallback, no Gemini)

1. Create and activate a virtualenv

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run app

   ```bash
   python app.py
   ```

3. Open http://localhost:5000 and try it out.

## Enable Gemini (Vertex AI)

To use Gemini you must configure Google Cloud credentials and set env vars:

1. Create a Google Cloud service account with Vertex AI access and download the JSON key.
2. Set the credentials env var:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json
export USE_GEMINI=1
export PROJECT_ID=your-gcp-project-id
# Optionally set location and GEMINI_MODEL
export LOCATION=us-central1
export GEMINI_MODEL=gemini-1.0
```

3. Install the Vertex SDK (already in `requirements.txt`) and run the app as before.

Notes:
- The server attempts to parse a JSON object returned by the model. If parsing fails, the raw response is returned in the `explanation` field.

## Using an API key instead of a service account (optional)

You can set `GEMINI_API_KEY` to call the Generative Language REST endpoint directly. Example:

```bash
export GEMINI_API_KEY="your_api_key"
export GEMINI_MODEL="gemini-1.0"  # optional
```

If `GEMINI_API_KEY` is set, the app uses it in preference to the Vertex SDK and makes a secure HTTPS POST to the Generative API. Keep your key secret — use a secrets manager or a local `.env` file that is included in `.gitignore`.

### Enforcing Gemini-only behavior
Set `REQUIRE_GEMINI=1` to make the server *require* Gemini for sentiment analysis — the server will return an error if Gemini is not configured or if model calls fail. This disables the local fallback analyzer and is useful for environments that must use the cloud model.

### If a key was exposed in chat
If you accidentally pasted a key (do not paste it in chat), revoke it immediately in the Google Cloud Console: go to **APIs & Services → Credentials**, find the API key, delete or regenerate it, and create a new one with appropriate restrictions (HTTP referrers / IPs). Do NOT use an exposed key in production.

## Files
- `app.py` — Flask backend, `/api/sentiment` endpoint
- `templates/index.html` — Simple SPA
- `static/main.js`, `static/style.css` — Client logic & styles

## Security
- Do not commit your service account keys; use secure secret management.

## License
MIT — feel free to modify.
