# AI-Powered Phishing Email Detector

A local web app that analyzes an email's sender, subject and body for phishing
indicators. It combines transparent rule-based checks with a local AI model
(Ollama) and shows an explainable 0-100 risk score. Results are **advisory only**.

## Features

- Input form with validation and size limits
- 6 rule-based indicators (urgency, threats, credential requests, payment requests,
  suspicious URLs, sender/domain mismatch)
- Local AI analysis through Ollama with timeout and error handling
- Risk score 0-100 with Low / Medium / High / Critical categories
- Falls back to rules-only scoring if the AI is unavailable
- Scan history in SQLite with search, filter, detail view and delete
- Download reports as JSON or text
- Security headers, escaped output, redacted logs

## Screenshots

![Home](docs/home.png)
![High risk result](docs/result-high.png)
![History](docs/history.png)

## Architecture

| Part | Responsibility |
|---|---|
| Frontend (HTML/CSS/JS) | Form, results, history, status bar |
| Flask backend (`app/routes.py`) | Web routes and request flow |
| Rule engine (`app/rules.py`) | Deterministic indicators, max 60 points |
| Ollama client (`app/ollama_client.py`) | Health check, prompt, validation of AI output |
| Scoring (`app/scoring.py`) | Combines rules (0-60) + AI (0-40) |
| SQLite (`app/database.py`) | Scan history, parameterized queries |

Flask was chosen over FastAPI because it is simpler for a small server-rendered app.

## Scoring

Final score = rule points (max 60) + AI points (AI risk score x 0.4, max 40), clamped to 0-100.

| Score | Category |
|---|---|
| 0-24 | Low |
| 25-49 | Medium |
| 50-74 | High |
| 75-100 | Critical |

These thresholds are illustrative, not a validated security standard.
Risk score (how dangerous the email looks) is different from AI confidence
(how sure the model is).

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com)
- Git

## Setup

```bash
git clone <your-repository-url>
cd <repository-folder>
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt
```

Copy the settings file:

```bash
copy .env.example .env         # Windows
cp .env.example .env           # Mac/Linux
```

Pull the tested model:

```bash
ollama pull llama3.2:3b
```

**Tested model:** `llama3.2:3b`

## Run

Make sure Ollama is running, then:

```bash
python run.py
```

Open http://127.0.0.1:5000. The database is created automatically in `instance/`.

## Tests

```bash
python -m pytest -v
```

Result: `<your number> passed`. Ollama is mocked, so tests run without it.

## Security and privacy

- Inputs are trimmed, required and length-limited; requests over 100 KB are rejected
- Output is auto-escaped by Jinja2
- All SQL uses `?` placeholders
- The email body is never stored
- Logs contain ids, scores and error types only
- The app never opens links, downloads attachments or sends email
- Server binds to 127.0.0.1 with debug off by default

See `docs/SECURITY.md`. Use synthetic or authorized emails only.

## Limitations

- Rules use fixed phrases, so new wording can be missed (false negatives)
- Legitimate emails with urgent language can be flagged (false positives)
- Small local models can be inconsistent or fooled by prompt injection
- No login or CSRF protection: for local single-user use only
- Sender and subject are stored unencrypted in `instance/scans.db`

## Troubleshooting

| Problem | Fix |
|---|---|
| "Ollama is not running" | Start the Ollama app or run `ollama serve` |
| "Model not found" | Run `ollama pull llama3.2:3b` |
| AI timeout | Run again (first run loads the model) or raise `OLLAMA_TIMEOUT` |
| `No module named ...` | Activate `venv` and run `pip install -r requirements.txt` |
| Port 5000 in use | Change the port in `run.py` |