"""
config.py — Loads settings.yaml + .env into a typed AppConfig object.

Single instance `cfg` is imported across the entire application:
    from src.config import cfg
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

_ROOT = Path(__file__).parent.parent

@dataclass(frozen=True)
class LLMConfig:
    model:                   str
    analyst_temperature:     float
    synthesiser_temperature: float
    max_log_tokens:          int


@dataclass(frozen=True)
class EmbeddingsConfig:
    model: str


@dataclass(frozen=True)
class RetrieverConfig:
    top_k:         int
    chunk_size:    int
    chunk_overlap: int


@dataclass(frozen=True)
class PathsConfig:
    logs:      Path
    docs:      Path
    chroma_db: Path


@dataclass(frozen=True)
class AppConfig:
    llm:            LLMConfig
    embeddings:     EmbeddingsConfig
    retriever:      RetrieverConfig
    paths:          PathsConfig
    groq_api_key:   str
    google_api_key: str

    def validate(self) -> None:
        missing = []
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY   → https://console.groq.com")
        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY → https://aistudio.google.com")
        if missing:
            raise EnvironmentError(
                "\n\n❌  Missing keys in .env:\n\n    "
                + "\n    ".join(missing)
                + "\n\n    Copy .env.example → .env and add your keys.\n"
            )


def _load() -> AppConfig:
    cfg_file = _ROOT / "config" / "settings.yaml"
    if not cfg_file.exists():
        raise FileNotFoundError(f"Config not found: {cfg_file}")

    raw = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))

    return AppConfig(
        llm=LLMConfig(**raw["llm"]),
        embeddings=EmbeddingsConfig(**raw["embeddings"]),
        retriever=RetrieverConfig(**raw["retriever"]),
        paths=PathsConfig(
            logs      = _ROOT / raw["paths"]["logs"],
            docs      = _ROOT / raw["paths"]["docs"],
            chroma_db = _ROOT / raw["paths"]["chroma_db"],
        ),
        groq_api_key   = os.getenv("GROQ_API_KEY",   ""),
        google_api_key = os.getenv("GOOGLE_API_KEY", ""),
    )


cfg = _load()
