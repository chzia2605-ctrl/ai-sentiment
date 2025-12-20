import os
import json
import re
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Config via env vars
USE_GEMINI = os.environ.get("USE_GEMINI", "0") == "1"
PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("LOCATION", "us-central1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "text-bison@001")  # override as needed
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # optional API key (set via env; do NOT paste keys in chat)
# If set to 1, the server will REQUIRE Gemini and will not fall back to the local analyzer
REQUIRE_GEMINI = os.environ.get("REQUIRE_GEMINI", "0") == "1"


def call_gemini(prompt: str) -> str:
    """Try to call Gemini / Vertex AI via the Vertex SDK.
    Requires Google Cloud credentials set (e.g. GOOGLE_APPLICATION_CREDENTIALS).
    """
    try:
        # Vertex AI Python library (preview) usage
        import vertexai
        from vertexai.preview.language_models import TextGenerationModel

        if not PROJECT_ID:
            raise RuntimeError("PROJECT_ID environment variable must be set to use Gemini.")

        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = TextGenerationModel.from_pretrained(GEMINI_MODEL)
        response = model.predict(prompt, max_output_tokens=512)
        return response.text
    except Exception as e:
        # Bubble up a helpful message
        raise RuntimeError(
            "Gemini call failed. Ensure Google credentials are configured and the Vertex SDK is installed. "
            f"Original error: {e}"
        )


def call_gemini_via_api_key(api_key: str, prompt: str, model: str) -> str:
    """Call the Generative Language REST endpoint with an API key.
    Note: model names like 'text-bison@001' or 'gemini-1.0' may be used depending on availability.
    The function returns the text output from the first candidate, or raises RuntimeError on failure.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta2/models/{model}:generate?key={api_key}"
        payload = {
            "prompt": {"text": prompt},
            "temperature": 0.0,
            "max_output_tokens": 512,
        }
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        j = resp.json()
        # Try common response shapes
        # new API: j.get('candidates', [])[0].get('output')
        if isinstance(j, dict):
            candidates = j.get("candidates")
            if candidates and isinstance(candidates, list) and candidates[0].get("output"):
                return candidates[0]["output"]
            # older/similar shapes
            output = j.get("output") or j.get("response")
            if output and isinstance(output, str):
                return output
        # Fallback return as text
        return json.dumps(j)
    except Exception as e:
        raise RuntimeError(f"Gemini API-key request failed: {e}")


def fallback_sentiment(text: str):
    """Negation-aware rule-based fallback sentiment analyzer.

    - Tokenizes words, matches against positive/negative lexicons
    - Detects simple negations ("not", "no", "never", "n't") within a small window
    - Flips polarity of words when preceded by negation
    """
    positives = {"good", "great", "awesome", "fantastic", "love", "like", "happy", "excellent"}
    negatives = {"bad", "terrible", "hate", "awful", "worst", "sad", "angry", "disappoint"}
    negation_words = {"not", "no", "never", "n't", "none", "hardly", "rarely", "barely"}

    tokens = re.findall(r"\w+", text.lower())
    pos = 0
    neg = 0

    for i, tok in enumerate(tokens):
        if tok in positives:
            window = tokens[max(0, i - 3):i]
            if any(n in window for n in negation_words):
                neg += 1
            else:
                pos += 1
        if tok in negatives:
            window = tokens[max(0, i - 3):i]
            if any(n in window for n in negation_words):
                pos += 1
            else:
                neg += 1

    total = pos + neg
    if total == 0:
        sentiment = "neutral"
        score = 0.5
    else:
        # Map polarity difference to score in [0..1], where >0.5 is positive
        ratio = (pos - neg) / total
        score = max(0.0, min(1.0, 0.5 + 0.5 * ratio))
        if pos == neg:
            sentiment = "neutral"
        elif pos > neg:
            sentiment = "positive"
        else:
            sentiment = "negative"

    explanation = f"Fallback analyzer: {pos} positive words, {neg} negative words (negation-aware)."
    return {"sentiment": sentiment, "score": round(score, 3), "explanation": explanation}


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/api/status')
def status():
    """Return a small status object indicating whether Gemini is enabled and which mode is in use.
    Does NOT expose secrets or API keys.
    """
    if GEMINI_API_KEY:
        mode = "api_key"
        enabled = True
    elif USE_GEMINI:
        mode = "vertex_sdk"
        enabled = True
    else:
        mode = "fallback"
        enabled = False
    return jsonify({
        "gemini_enabled": enabled,
        "mode": mode,
        "model": GEMINI_MODEL,
        "require_gemini": REQUIRE_GEMINI,
    })


@app.route("/api/sentiment", methods=["POST"])
def sentiment():
    data = request.get_json() or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "No text provided."}), 400

    # Prioritize GEMINI_API_KEY (API key flow), then Vertex SDK via USE_GEMINI, otherwise fallback
    prompt = (
        "You are a sentiment analysis assistant. Classify the sentiment of the text into 'positive', 'neutral', or 'negative'. "
        "Return a JSON object with keys: sentiment (string), score (float 0..1), explanation (short string).\n\n"
        f"Text: {json.dumps(text)}"
    )

    # Use Gemini if configured. If REQUIRE_GEMINI is set, return an error when Gemini is not available.
    if GEMINI_API_KEY:
        try:
            raw = call_gemini_via_api_key(GEMINI_API_KEY, prompt, GEMINI_MODEL)
            m = re.search(r"(\{[\s\S]*\})", raw)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                    return jsonify(parsed)
                except Exception:
                    return jsonify({"sentiment": "unknown", "score": 0.0, "explanation": raw})
            else:
                return jsonify({"sentiment": "unknown", "score": 0.0, "explanation": raw})
        except Exception as e:
            # If Gemini is required, surface the error; otherwise fall back
            if REQUIRE_GEMINI:
                return jsonify({"error": f"Gemini (API key) unavailable: {e}"}), 502
            fback = fallback_sentiment(text)
            fback["explanation"] = f"Gemini (API key) unavailable: {e}. {fback['explanation']}"
            return jsonify(fback)
    elif USE_GEMINI:
        try:
            raw = call_gemini(prompt)
            m = re.search(r"(\{[\s\S]*\})", raw)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                    return jsonify(parsed)
                except Exception:
                    return jsonify({"sentiment": "unknown", "score": 0.0, "explanation": raw})
            else:
                return jsonify({"sentiment": "unknown", "score": 0.0, "explanation": raw})
        except Exception as e:
            if REQUIRE_GEMINI:
                return jsonify({"error": f"Gemini (Vertex SDK) unavailable: {e}"}), 502
            fback = fallback_sentiment(text)
            fback["explanation"] = f"Gemini unavailable: {e}. {fback['explanation']}"
            return jsonify(fback)
    else:
        if REQUIRE_GEMINI:
            return jsonify({"error": "Gemini is not configured on the server. Set GEMINI_API_KEY or enable the Vertex SDK (USE_GEMINI=1)."}), 400
        return jsonify(fallback_sentiment(text))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
