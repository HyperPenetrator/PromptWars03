# EcoTrace 🌱

A smart carbon footprint tracker powered by Gemini AI. Track your daily emissions across transport, energy, diet, and shopping — then get personalized, AI-powered suggestions to reduce your environmental impact.

## Features

- **📊 Dashboard** — Real-time carbon summary with category breakdown charts
- **📝 Activity Logging** — Log emissions across 4 categories with auto CO₂e calculation
- **🤖 AI Insights** — Gemini-powered analysis with ranked, personalized suggestions
- **🎯 Goals** — Set monthly CO₂e reduction targets and track progress
- **📈 Trends** — 7-day line chart showing emission patterns over time

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5 + CSS + Vanilla JS |
| Backend | Python 3.11 + FastAPI |
| Database | SQLite (via SQLModel) |
| AI | Gemini 1.5 Flash |
| Charts | Chart.js (CDN) |

## Setup

```bash
cd ecotrace
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Add your GEMINI_API_KEY
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

## Run Tests

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/logs` | Create a new emission log |
| `GET` | `/logs?days=7` | Get recent logs |
| `GET` | `/logs/summary?days=7` | Aggregated CO₂e summary |
| `DELETE` | `/logs/{id}` | Delete a log entry |
| `POST` | `/insights` | Generate AI insights |
| `GET` | `/insights/weekly` | Weekly summary with comparison |
| `POST` | `/goals` | Create a reduction goal |
| `GET` | `/goals` | List goals with progress |
| `PATCH` | `/goals/{id}` | Update a goal |
| `DELETE` | `/goals/{id}` | Delete a goal |

## Submission Notes

- **Vertical:** Individual Environmental Awareness
- **Branch:** main (single branch)
- **Repo size:** < 10 MB (SQLite DB excluded via .gitignore)
