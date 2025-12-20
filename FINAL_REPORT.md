(AI VIRTUAL MOUSE)
(HAFS UR REHMAN)
(S24BDOCS7M08031)

[Project Documentation]



Version: (1)	Date: 12-12-25

# AI Sentiment — Final Project Report

**Student:** HAFS UR REHMAN  
**Project Title:** AI Sentiment — Minimal Gemini-enabled Sentiment SPA  
**Version:** 1.0  
**Date:** December 20, 2025

---

## Table of Contents
- 1. Introduction
- 2. Scope & Purpose
- 3. Definitions & References
- 4. Product Overview & Features
- 5. Environment & Configuration
- 6. API & Endpoints
- 7. Architecture & Design
- 8. Implementation Details
- 9. Testing & Validation
- 10. Security & Operational Notes
- 11. Limitations & Future Work
- 12. Appendix — Useful Commands & Examples

---

## 1. Introduction

This document is the final project report for **AI Sentiment**, a minimal single-page web application that performs sentiment analysis on user text using an optional Gemini (Generative AI) integration and a local fallback analyzer.

The goal of the project is to provide a simple, secure, and extendable example of a Flask-backed SPA that can call a cloud LLM (Gemini) when configured but degrades gracefully to a deterministic local analyzer otherwise.

## 2. Scope & Purpose

- **Purpose:** Demonstrate a working minimal pipeline for single-page sentiment analysis, with both cloud model integration (Gemini) and a local fallback.
- **Audience:** Project reviewers, maintainers, developers, and evaluators.
- **Scope:** UI (HTML/CSS/JS), backend (Flask), optional Gemini integration (API key or Vertex SDK), and local negation-aware rule-based fallback.

## 3. Definitions & References

- **Gemini** — Google generative language model (accessible via Generative REST API with an API key or via Vertex SDK/service account).
- **Flask** — Python web microframework.
- **SPA** — Single Page Application (static frontend served by Flask).

**References:**
- Primary repo files: `app.py`, `templates/index.html`, `static/main.js`, `static/style.css`, `README.md`, `requirements.txt`.
- Google Generative Language API docs and Vertex AI docs.

## 4. Product Overview & Features

**Core features:**
- Single-page HTML UI to submit text and view sentiment.
- Backend endpoint `POST /api/sentiment` that returns JSON `{sentiment, score, explanation}`.
- Gemini integration modes:
  - **API-key mode** (via `GEMINI_API_KEY`) — calls Generative REST API.
  - **Vertex SDK mode** (via `USE_GEMINI=1`, `PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`) — uses service account.
- **Fallback** to local analyzer when Gemini is unavailable (unless `REQUIRE_GEMINI=1`).
- Local fallback sentiment analyzer with simple negation-aware rules.
- Polished UI: colored sentiment card, emojis/SVG icons, confetti for positive results, copy/share actions, raw JSON view.

## 5. Environment & Configuration

**Files:** `.env.example` contains example env variables. `.env` is ignored and used for local development.

**Key env variables:**
- `USE_GEMINI` (0|1) — enable Vertex SDK mode.
- `GEMINI_API_KEY` — optional API key to call Generative REST API.
- `GEMINI_MODEL` — model name (default `text-bison@001`, can be changed).
- `PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` — for Vertex SDK.
- `REQUIRE_GEMINI` (0|1) — if `1`, server returns an error instead of falling back.
- `PORT` — server port (default 5000).

**Install & run:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Optional: set env vars or create .env.
./start.sh    # or `make start`
# Open http://localhost:5000
```

## 6. API & Endpoints

- `GET /` — Serves the SPA (`templates/index.html`).
- `POST /api/sentiment` — Accepts JSON `{text: "..."}`. Returns JSON `{sentiment, score, explanation}`. Uses Gemini when available; falls back to local analyzer.
- `GET /api/status` — Returns server status (Gemini configured, mode, model, require_gemini) without exposing secrets.

**Example request:**
```bash
curl -X POST http://127.0.0.1:5000/api/sentiment \
  -H 'Content-Type: application/json' \
  -d '{"text":"I love this product"}'
```

## 7. Architecture & Design

**Architecture:** Simple client-server SPA with stateless request handling for sentiment classification.

**Components:**
- Frontend: `templates/index.html`, `static/main.js`, `static/style.css` (UI, fetches API, renders sentiment card).
- Backend: `app.py` (Flask) — orchestrates Gemini calls and fallback analyzer.
- Optional: Vertex SDK (`vertexai`) or REST via `requests` using `GEMINI_API_KEY`.

**Design choices:**
- Prioritize security: do not log or expose API keys; status endpoint never returns secrets.
- Graceful degradation: server falls back unless `REQUIRE_GEMINI=1`.
- Simplicity and readability: minimal dependencies and a straightforward flow.

## 8. Implementation Details

**Key files and responsibilities:**
- `app.py` — routing, Gemini integration (`call_gemini` via SDK and `call_gemini_via_api_key` via REST), local fallback `fallback_sentiment` (negation-aware), and `REQUIRE_GEMINI` enforcement.
- `templates/index.html` — SPA layout and result card.
- `static/main.js` — frontend logic: status check, submit text, render results, confetti, copy/share.
- `static/style.css` — refined UI styles and responsive layout.
- `start.sh` / `Makefile` — convenient run scripts.

**Notable behavior:**
- Fallback sentiment analyzer tokenizes text and detects negation words (e.g., `not`, `no`, `never`) and flips polarity within a small window.
- Gemini usage preference: if `GEMINI_API_KEY` is present it is used first; otherwise `USE_GEMINI=1` enables the Vertex SDK flow.
- If `REQUIRE_GEMINI=1` and Gemini calls fail, the server returns an error (HTTP 4xx/5xx) rather than falling back.

**Current status of Gemini integration:**
- The app supports both the Generative REST API (API key) and Vertex SDK (service account).
- During development, cloud diagnostics returned `403 PERMISSION_DENIED` for model-list and `404 Not Found` for generate calls with certain model names — these indicate cloud-side permission / model availability issues that must be resolved in the Google Cloud console (enable API, ensure billing, check key restrictions or service account permissions).

## 9. Testing & Validation

**Manual & automated test cases to validate behavior:**
- Basic API: submit positive/neutral/negative text and verify sentiment and score.
- Fallback tests: confirm negation behavior (`"not good"` → negative).
- Gemini status tests: confirm `/api/status` reflects configuration.
- Error paths: simulate Gemini 404/403 and verify fallback or error when `REQUIRE_GEMINI=1`.

**Sample tests run during development (manual):**
```bash
curl -X POST http://127.0.0.1:5000/api/sentiment \
  -H 'Content-Type: application/json' \
  -d '{"text":"I love this"}'
# Expect: positive

curl -X POST http://127.0.0.1:5000/api/sentiment \
  -H 'Content-Type: application/json' \
  -d '{"text":"you are not good"}'
# Expect: negative (fallback negation-aware)
```

**Suggested automated tests (future):**
- Unit tests for the fallback analyzer and `app.py` endpoints using `pytest`.
- Mock Gemini responses (HTTP or Vertex SDK) to exercise success, transient errors, and permanent failures.
- Add GitHub Actions to run tests on push.

## 10. Security & Operational Notes

- **Do not commit keys** — `.gitignore` and `.env` usage is configured to avoid committing API keys or service account JSON.
- **If a key is leaked** (for example: posted in a chat), revoke it immediately in Google Cloud Console and generate a new one.
- **Production recommendations:** prefer service accounts + Vertex SDK and store secrets in a secrets manager or CI secret store.
- **Authentication & authz:** This demo is built for local use with no authentication; add auth for multi-user or production deployments.

## 11. Limitations & Future Work

**Short-term improvements:**
- Add unit tests (mocked Gemini and fallback).
- Add `Dockerfile` and GitHub Actions CI pipeline.
- Persist user preferences or usage telemetry (optional feature).
- Replace simple rule-based fallback with a small pre-trained transformer for better accuracy.
- Internationalization and additional accessibility refinements (keyboard navigation, screen reader labels).

**Longer-term / research ideas:**
- Add an evaluation suite with labeled sentiment data and automated periodic quality checks.
- Add rate-limiting, quotas, and usage tracking for API access cost control.

## 12. Appendix — Useful Commands & Examples

**Start app (local):**
```bash
./start.sh
# or
make start
```

**Check status:**
```bash
curl -sS http://127.0.0.1:5000/api/status | jq
```

**Test sentiment endpoint:**
```bash
curl -sS -X POST http://127.0.0.1:5000/api/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text":"I hate this"}' | jq
```

**Test Generative REST (example — replace the model with one returned by list):**
```bash
export GEMINI_API_KEY="YOUR_KEY"
curl -sS -X POST "https://generativelanguage.googleapis.com/v1/models/text-bison@001:generate?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":{"text":"Classify sentiment: I love this product."}}' | jq
```

---

**Author notes:** This project is intentionally minimal and educational. The code is organized for clarity and extendability — a good base to add model-backed classification, CI, and deployment pipelines.

© 2025 — AI Sentiment Project
