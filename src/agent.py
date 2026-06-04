"""
agent.py — LangGraph multi-agent workflow.

Graph:  retriever  →  analyst  →  synthesiser  →  END
"""

from __future__ import annotations

import json
import operator
from functools import partial
from typing import Annotated

from langchain_community.vectorstores import Chroma
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import MarkdownTextSplitter
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.config import cfg

class AgentState(TypedDict):
    question:     str
    rag_context:  str
    data_context: str
    final_answer: str
    messages:     Annotated[list, operator.add]

def _llm(temperature: float) -> ChatGroq:
    return ChatGroq(
        model=cfg.llm.model,
        temperature=temperature,
        api_key=cfg.groq_api_key,
    )

def _embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=cfg.embeddings.model,
        google_api_key=cfg.google_api_key,
    )

def build_vector_store() -> Chroma:
    """Chunk markdown docs → embed → persist to ChromaDB."""
    print("📚  Indexing knowledge base ...")
    splitter = MarkdownTextSplitter(
        chunk_size=cfg.retriever.chunk_size,
        chunk_overlap=cfg.retriever.chunk_overlap,
    )
    docs: list = []
    for path in sorted(cfg.paths.docs.glob("*.md")):
        chunks = splitter.create_documents(
            texts=[path.read_text(encoding="utf-8")],
            metadatas=[{"source": path.name}],
        )
        docs.extend(chunks)
        print(f"   ✓  {path.name}  ({len(chunks)} chunks)")

    if not docs:
        raise FileNotFoundError(f"No markdown files found in {cfg.paths.docs}")

    store = Chroma.from_documents(
        documents=docs,
        embedding=_embeddings(),
        persist_directory=str(cfg.paths.chroma_db),
    )
    print(f"✅  {len(docs)} chunks indexed\n")
    return store

def load_pipeline_runs() -> list[dict]:
    """Load ADF pipeline run logs from JSON."""
    with open(cfg.paths.logs, encoding="utf-8") as fh:
        return json.load(fh)

def _retriever(state: AgentState, *, store: Chroma) -> AgentState:
    """RAG: semantic search over runbooks and SLA docs."""
    print("🔍  [Retriever] Searching knowledge base ...")
    docs = store.as_retriever(
        search_kwargs={"k": cfg.retriever.top_k}
    ).invoke(state["question"])
    print(f"   Retrieved {len(docs)} chunks")
    return {**state, "rag_context": "\n\n---\n\n".join(d.page_content for d in docs)}

def _analyst(state: AgentState, *, runs: list[dict]) -> AgentState:
    """Structured analysis: extract relevant facts from pipeline run logs."""
    print("📊  [Analyst] Querying pipeline run data ...")
    prompt = (
        "You are a data pipeline analyst reviewing Azure Data Factory run logs.\n\n"
        f"PIPELINE RUN DATA:\n{json.dumps(runs, indent=2)[:cfg.llm.max_log_tokens]}\n\n"
        f"QUESTION: {state['question']}\n\n"
        "Extract only facts directly relevant to this question — pipeline names, "
        "statuses, error codes, messages, durations, row counts, timestamps. "
        "Be specific. If nothing is relevant, say so."
    )
    response = _llm(cfg.llm.analyst_temperature).invoke([HumanMessage(content=prompt)])
    print("   Analyst complete")
    return {**state, "data_context": response.content}

def _synthesiser(state: AgentState) -> AgentState:
    """Combine RAG context + data analysis into a final actionable answer."""
    print("🧠  [Synthesiser] Generating answer ...")
    prompt = (
        "You are an expert Data Platform Operations engineer.\n\n"
        f"RUNBOOK & SLA CONTEXT:\n{state['rag_context']}\n\n"
        f"PIPELINE DATA ANALYSIS:\n{state['data_context']}\n\n"
        f"QUESTION: {state['question']}\n\n"
        "Provide a structured answer that:\n"
        "1. Directly answers the question\n"
        "2. Cites pipeline names, error codes, or timestamps\n"
        "3. Lists concrete resolution steps\n"
        "4. Flags SLA breaches or downstream cascade risks\n\n"
        "Use bullet points for action items. Be concise but complete."
    )
    response = _llm(cfg.llm.synthesiser_temperature).invoke([HumanMessage(content=prompt)])
    print("✅  Answer ready\n")
    return {
        **state,
        "final_answer": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)],
    }

def build_graph(store: Chroma, runs: list[dict]):
    """Compile the LangGraph state machine."""
    g = StateGraph(AgentState)
    g.add_node("retriever",   partial(_retriever,   store=store))
    g.add_node("analyst",     partial(_analyst,     runs=runs))
    g.add_node("synthesiser", _synthesiser)
    g.set_entry_point("retriever")
    g.add_edge("retriever",   "analyst")
    g.add_edge("analyst",     "synthesiser")
    g.add_edge("synthesiser", END)
    return g.compile()

def ask(graph, question: str) -> str:
    """Ask a question, get the final answer string."""
    result = graph.invoke({
        "question":     question,
        "rag_context":  "",
        "data_context": "",
        "final_answer": "",
        "messages":     [HumanMessage(content=question)],
    })
    return result["final_answer"]