<div align="center">

# 🔧 Pipeline Intelligence Agent

**Natural language monitoring for Azure Data Factory pipelines.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-6C48C5?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Free](https://img.shields.io/badge/Cost-100%25%20Free-brightgreen?style=flat-square)]()

*Ask your pipelines anything. Get root cause, SLA impact, and resolution steps — in seconds.*

</div>

---

## The Problem

When an ADF pipeline fails at 2am, an on-call engineer spends an hour:
- Cross-referencing error codes against runbooks
- Determining if an SLA breach has occurred
- Tracing downstream cascade failures
- Figuring out who to call

This agent does all of that in plain English, instantly.

```
You:   "Why did the sales pipeline fail today?"

Agent: PL_IngestSalesData_Daily failed at 02:14 AEST (SqlFailedToConnect).
       A manual rerun at 03:32 also failed — confirming a firewall issue, not transient.
       This is a P1 SLA breach (deadline 03:00 AEST).
       PL_PowerBI_RefreshDatasets timeout at 06:00 is a direct downstream consequence.

       Action items:
       • Verify Azure SQL firewall rules for the ADF Integration Runtime
       • Confirm IR can reach sql-sales-prod.database.windows.net
       • Rerun PL_IngestSalesData_Daily after the fix
       • Notify sales-ops@company.com of the delay
```

---

## Architecture

```
User Question
     │
     ▼
LangGraph Orchestrator
     │
     ├─────────────────────────┐
     ▼                         ▼
Retriever Node            Analyst Node
RAG over runbooks         Queries pipeline
+ SLA docs                run logs (JSON)
(ChromaDB +               (Groq LLM)
Google Embeddings)
     │                         │
     └─────────────┬───────────┘
                   ▼
           Synthesiser Node
           Root cause + SLA impact
           + Resolution steps
           (Groq LLM)
                   │
          ┌────────┴────────┐
          ▼                 ▼
     FastAPI API       Streamlit UI
     /ask /runs        Chat interface
```

---

## Free Tool Stack

| Layer | Tool | Free Tier |
|---|---|---|
| LLM | [Groq](https://console.groq.com) — Llama 3.3 70B | 14,400 req/day |
| Embeddings | [Google AI Studio](https://aistudio.google.com) | Free tier |
| Vector Store | ChromaDB | Local, unlimited |
| Framework | LangChain + LangGraph | Open source |
| API | FastAPI | Open source |
| UI | Streamlit | Open source |

---

## Quick Start

### 1. Get free API keys

| Key | Where |
|-----|-------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API key |

### 2. Install

```bash
git clone https://github.com/YOUR_USERNAME/pipeline-intelligence-agent
cd pipeline-intelligence-agent
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Add your two keys to .env
```

### 4. Run

```bash
# CLI
python -m src.cli

# API + UI (two terminals)
python -m uvicorn src.api:app --reload --port 8000
python -m streamlit run src/ui.py

# Docker (one command)
docker-compose up --build
```

---

## Project Structure

```
pipeline-intelligence-agent/
│
├── config/
│   └── settings.yaml          # All tuneable settings (model, chunk size, etc.)
│
├── src/
│   ├── config.py              # Loads settings.yaml + .env → typed AppConfig
│   ├── agent.py               # LangGraph graph: retriever → analyst → synthesiser
│   ├── api.py                 # FastAPI REST API
│   ├── ui.py                  # Streamlit chat UI
│   └── cli.py                 # Command-line entry point
│
├── data/
│   ├── logs/pipeline_runs.json      # ADF run logs (Azure Monitor schema)
│   └── docs/
│       ├── pipeline_runbooks.md     # Per-pipeline error resolution guides
│       └── sla_policy.md           # SLA tiers and escalation matrix
│
├── .env.example               # API key template
├── .gitignore
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

**The design principle:** one file, one job.

| File | Job |
|------|-----|
| `config/settings.yaml` | What to tune |
| `.env` | Secrets only |
| `src/config.py` | Bridge between config and code |
| `src/agent.py` | Agent logic only |
| `src/api.py` | HTTP layer only |
| `src/ui.py` | UI only |
| `src/cli.py` | CLI only |

---

## API Reference

```bash
# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Why did the sales pipeline fail today?"}'

# List all runs
curl http://localhost:8000/runs

# Filter by status or domain
curl "http://localhost:8000/runs?status=Failed"
curl "http://localhost:8000/runs?domain=sales"
```

Interactive docs at **http://localhost:8000/docs**

---

## Author

**Mahitha Muppalaneni** — Data Engineer  
6+ years building enterprise ETL/ELT pipelines on Azure, AWS, and GCP.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/mahitha-muppalaneni)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/YOUR_USERNAME)

---

*MIT License*
