<div align="center">

# 🔧 Pipeline Intelligence Agent

**Ask your Azure Data Factory pipelines anything. In plain English.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-6C48C5?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-F55036?style=flat-square)](https://console.groq.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Free](https://img.shields.io/badge/Cost-100%25%20Free-brightgreen?style=flat-square)]()

*A production-grade LangGraph multi-agent system that diagnoses ADF pipeline failures,
detects SLA breaches, and recommends resolution steps — using only free, open-source tools.*

[**Quick Start**](#-quick-start) · [**Architecture**](#-architecture) · [**Tech Stack**](#-tech-stack)

</div>

---

## The Problem

Enterprise data teams manage dozens of Azure Data Factory pipelines across multiple business domains.
When a critical pipeline fails at 2am, an engineer spends an hour:
- Cross-referencing error logs against runbooks
- Identifying whether an SLA breach has occurred
- Tracing downstream cascade failures
- Determining the right escalation contact

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
┌─────────────────────────────────────────────────────────────────────┐
│                        User Question                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                            │
│              (compiled state machine — AgentState)                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│     Retriever Node        │   │            Analyst Node              │
│                           │   │                                      │
│  Semantic search over     │   │  Queries ADF pipeline run JSON       │
│  runbooks + SLA policy    │   │  (real Azure Monitor schema)         │
│                           │   │                                      │
│  ChromaDB vector store    │   │  Groq Llama 3.3 70B extracts        │
│  Google AI embeddings     │   │  relevant facts and error details    │
└──────────────────────────┘   └──────────────────────────────────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Synthesiser Node                                │
│                                                                      │
│  Combines RAG context + structured data analysis                     │
│  Groq Llama 3.3 70B → root cause + SLA impact + action steps        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│      FastAPI REST API     │   │         Streamlit Chat UI            │
│  POST /ask                │   │  Pipeline status sidebar             │
│  GET  /runs               │   │  Natural-language chat               │
│  GET  /health             │   │  Sample question buttons             │
└──────────────────────────┘   └──────────────────────────────────────┘
```

---

## Tech Stack

Every tool in this project is **free**. No credit card required anywhere.

| Layer | Tool | Free Tier |
|---|---|---|
| LLM | [Groq](https://console.groq.com) — Llama 3.3 70B | 14,400 req/day |
| Embeddings | [Google AI Studio](https://aistudio.google.com) | Free tier |
| Vector Store | ChromaDB | Local, unlimited |
| Framework | LangGraph + LangChain | Open source |
| API | FastAPI | Open source |
| UI | Streamlit | Open source |
| Observability | [LangSmith](https://smith.langchain.com) *(optional)* | Free tier agent tracing |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Two free API keys (setup takes ~5 minutes — see below)

### 1. Get your free API keys

<details>
<summary><b>Groq API Key</b> (your LLM — Llama 3.3 70B)</summary>

1. Go to **[console.groq.com](https://console.groq.com)**
2. Sign up with email or Google — no credit card
3. Left sidebar → **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_…`)

</details>

<details>
<summary><b>Google AI Studio Key</b> (your embeddings)</summary>

1. Go to **[aistudio.google.com](https://aistudio.google.com)**
2. Sign in with any Google account
3. Click **Get API key** → **Create API key**
4. Copy the key (starts with `AIza…`)

</details>

<details>
<summary><b>Langsmith API Key</b> (tracing)</summary>

1. Go to **[smith.langchain.com](https://smith.langchain.com)**
2. Sign in with any Google account
3. Click **Get API key** → **Create API key**
4. Copy the key (starts with `lsv2…`)

</details>

### 2. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/pipeline-intelligence-agent
cd pipeline-intelligence-agent
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Add your keys to .env
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

## 🔍 Observability

This project supports [LangSmith](https://smith.langchain.com) tracing out of the box — no code changes required.

Once enabled via `.env`, every agent run is fully traced:

- Each node execution — Retriever · Analyst · Synthesiser
- The exact prompt sent to Groq and the response received
- Token count and latency per LLM call
- Which runbook chunks ChromaDB retrieved and their similarity scores

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
│   ├── logs/
│   │   └── pipeline_runs.json      # 8 realistic ADF runs (Azure Monitor schema)
│   └── docs/
│       ├── pipeline_runbooks.md    # Per-pipeline runbooks with error resolution
│       └── sla_policy.md           # SLA tiers, escalation matrix, dependency chain
│
├── .env.example             # Environment variable template
├── .gitignore               # Protects .env and generated files
├── requirements.txt         # Pinned dependencies
├── Dockerfile               # Multi-stage build
└── docker-compose.yml       # API + UI with healthcheck
```

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

## 👤 Author

**Mahitha Muppalaneni**

Data Engineer with 6+ years building enterprise ETL/ELT pipelines on Azure, AWS, and GCP.
Specialist in ADF, Python, Power BI, and cloud-native data architectures.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/mahitha-muppalaneni)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/YOUR_USERNAME)

---

## 📄 License

MIT — free to use, modify, and distribute.