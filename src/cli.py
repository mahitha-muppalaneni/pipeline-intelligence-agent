"""
cli.py — Command-line entry point.

Usage:
    python -m src.cli
    python -m src.cli --question "Why did the sales pipeline fail?"
"""

from __future__ import annotations

import argparse
import sys

from src.agent import ask, build_graph, build_vector_store, load_pipeline_runs
from src.config import cfg

DEMOS = [
    "Why did the sales pipeline fail today, and has this happened before?",
    "Which pipelines have breached their SLA and what should I do?",
    "What caused the Power BI refresh to time out this morning?",
    "Give me a full failure report with recommended actions.",
]

def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline Intelligence Agent")
    parser.add_argument("--question", "-q", type=str, default=None)
    args = parser.parse_args()

    cfg.validate()

    store = build_vector_store()
    runs  = load_pipeline_runs()
    graph = build_graph(store, runs)

    if args.question:
        print(f"\n❓  {args.question}\n")
        print(ask(graph, args.question))
        return

    print("\n💬  Demo questions:\n")
    for i, q in enumerate(DEMOS, 1):
        print(f"    {i}. {q}")
    print()

    while True:
        raw = input("\nYou (1-4 for demo, your question, or 'exit'): ").strip()
        if raw.lower() in ("exit", "quit"):
            sys.exit(0)
        if raw.isdigit() and 1 <= int(raw) <= len(DEMOS):
            question = DEMOS[int(raw) - 1]
            print(f"\n❓  {question}")
        elif raw:
            question = raw
        else:
            continue
        print()
        print(ask(graph, question))
        print("─" * 60)

if __name__ == "__main__":
    main()
