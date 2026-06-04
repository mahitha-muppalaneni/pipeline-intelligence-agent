"""
ui.py — Streamlit chat interface.

Run:
    streamlit run src/ui.py
"""

from __future__ import annotations

import os
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Pipeline Intelligence Agent", page_icon="🔧", layout="wide")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔧 Pipeline Intelligence Agent")
    st.caption("Groq · Google AI · LangGraph · ChromaDB")
    st.divider()
    st.markdown("### Pipeline Status")
    try:
        data = requests.get(f"{API}/runs", timeout=5).json()
        runs = data["runs"]
        statuses = [r["status"] for r in runs]
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ OK",      statuses.count("Succeeded"))
        c2.metric("❌ Failed",  statuses.count("Failed"))
        c3.metric("⏰ Timeout", statuses.count("TimedOut"))
        st.divider()
        icons = {"Succeeded": "✅", "Failed": "❌", "TimedOut": "⏰"}
        sla   = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        for r in runs:
            name = r["pipeline_name"].replace("PL_", "")
            st.markdown(
                f"{icons.get(r['status'],'❓')} **{name}**  \n"
                f"{sla.get(r['sla'],'⚪')} `{r['sla']}` · {r['run_start'][:10]}"
            )
            st.divider()
    except Exception:
        st.warning("API offline.\n\n`uvicorn src.api:app --reload`")

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("# 🔧 Pipeline Intelligence Agent")
st.caption("Ask anything about your ADF pipeline health in plain English.")

SAMPLES = [
    "Why did the sales pipeline fail today?",
    "Which pipelines breached their SLA?",
    "What caused the Power BI timeout?",
    "Full failure report with actions.",
    "Is the inventory failure related to SAP maintenance?",
]

cols = st.columns(3)
for i, q in enumerate(SAMPLES):
    if cols[i % 3].button(q, use_container_width=True):
        st.session_state.prefill = q

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask about your pipelines…") or st.session_state.pop("prefill", "")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                r = requests.post(f"{API}/ask", json={"question": question}, timeout=90)
                r.raise_for_status()
                answer = r.json()["answer"]
            except requests.exceptions.ConnectionError:
                answer = "❌ API offline. Run: `uvicorn src.api:app --reload --port 8000`"
            except Exception as e:
                answer = f"❌ Error: {e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
