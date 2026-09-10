"""Optional Groq/Llama rewriting for advisor answers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
CACHE_FILE = PROJECT_ROOT / "data" / "llm_cache.json"

load_dotenv(dotenv_path=ENV_FILE)


def _load_cache() -> dict[str, str]:
    """Load previously generated LLM answers."""
    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (json.JSONDecodeError, OSError):
        pass

    return {}


def _save_cache(cache: dict[str, str]) -> None:
    """Save generated LLM answers locally."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2, ensure_ascii=False)


def _create_cache_key(
    question: str,
    advisor_result: dict[str, Any],
) -> str:
    """Create a stable cache key from the question and advisor result."""
    cache_content = {
        "question": question.strip().lower(),
        "intent": advisor_result.get("intent", "general"),
        "component": advisor_result.get("component", "unknown"),
        "answer": advisor_result.get("answer", ""),
        "evidence": advisor_result.get("evidence", [])[:3],
    }

    serialized = json.dumps(
        cache_content,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def improve_answer_with_llm(
    question: str,
    advisor_result: dict[str, Any],
) -> str:
    """
    Improve the offline answer using Groq/Llama.

    The LLM receives only:
    - the user question;
    - detected intent;
    - detected component;
    - structured knowledge-base result;
    - top three retrieved manual chunks.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to the project .env file."
        )

    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError(
            "The groq package is not installed. "
            "Run: pip install groq"
        ) from exc

    # Read the offline advisor result.
    intent = advisor_result.get("intent", "general")
    component = advisor_result.get("component", "unknown")
    original_answer = advisor_result.get("answer", "")
    tools_materials = advisor_result.get("tools_materials", [])
    safety_warnings = advisor_result.get("safety_warnings", [])
    evidence = advisor_result.get("evidence", [])

    # Create the structured knowledge sent to the LLM.
    knowledge_base_result = {
        "answer": original_answer,
        "tools_materials": tools_materials,
        "safety_warnings": safety_warnings,
    }

    # Send only the top three retrieved chunks.
    top_chunks: list[dict[str, Any]] = []

    for item in evidence[:3]:
        if not isinstance(item, dict):
            continue

        top_chunks.append(
            {
                "chunk_id": item.get("chunk_id", "unknown"),
                "text": item.get("text", ""),
            }
        )

    cache = _load_cache()
    cache_key = _create_cache_key(question, advisor_result)

    # Do not call Groq again for the same input.
    if cache_key in cache:
        return cache[cache_key]

    prompt = f"""
You are a wind turbine maintenance advisor.

Answer only using the provided context.
Do not invent information.

If the context is insufficient, say exactly:
"The manual does not provide enough information."

Improve the offline answer so that it directly answers the user's
question in clear and simple language.

Always include:
- Maintenance or inspection steps
- Tools/materials, if available
- Safety warnings, if available
- Evidence chunk IDs

Do not mention information that is not supported by either the
structured knowledge or the retrieved chunks.

Question:
{question}

Detected intent:
{intent}

Detected component:
{component}

Structured knowledge:
{json.dumps(knowledge_base_result, indent=2, ensure_ascii=False)}

Retrieved manual chunks:
{json.dumps(top_chunks, indent=2, ensure_ascii=False)}
""".strip()

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=500,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Use only the supplied wind-turbine maintenance "
                        "context. Give a short, grounded answer. Never "
                        "invent instructions, tools, or warnings."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

    except Exception as exc:
        raise RuntimeError(f"Groq request failed: {exc}") from exc

    improved = response.choices[0].message.content

    if not improved or not improved.strip():
        raise RuntimeError("The LLM returned an empty answer.")

    improved = improved.strip()

    # Save the response so the same input does not call Groq again.
    cache[cache_key] = improved
    _save_cache(cache)

    return improved