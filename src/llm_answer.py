"""Optional Groq rewriting for advisor answers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


def improve_answer_with_llm(
    question: str,
    advisor_result: dict[str, Any],
) -> str:
    """
    Rewrite the grounded offline answer using Groq.

    The offline advisor remains the technical source of truth.
    The LLM only improves wording and presentation.
    """

    # ---------------------------------------------------------
    # 1. Check API key
    # ---------------------------------------------------------

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to the project .env file."
        )

    # ---------------------------------------------------------
    # 2. Import Groq
    # ---------------------------------------------------------

    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError(
            "The groq package is not installed. "
            "Run: pip install groq"
        ) from exc

    # ---------------------------------------------------------
    # 3. Get grounded offline answer
    # ---------------------------------------------------------

    original_answer = str(
        advisor_result.get("answer", "")
    ).strip()

    if not original_answer:
        raise RuntimeError(
            "The offline advisor returned no answer to rewrite."
        )

    intent = str(
        advisor_result.get("intent", "general")
    )

    component = str(
        advisor_result.get("component", "unknown")
    )

    print("CALLING GROQ API...")

    # ---------------------------------------------------------
    # 4. Build controlled rewriting prompt
    # ---------------------------------------------------------

    prompt = f"""
You are given an OFFLINE ANSWER produced by an
evidence-grounded wind turbine maintenance advisor.

Rewrite ONLY that answer to make it clearer and easier to read.

IMPORTANT RULES:

1. Preserve every technical fact from the OFFLINE ANSWER.

2. Do NOT add any new:
   - maintenance steps
   - inspection steps
   - troubleshooting steps
   - tools
   - materials
   - safety instructions

3. Do NOT remove important technical information.

4. Do NOT independently answer the user's question.

5. Do NOT mention:
   - evidence
   - sources
   - chunks
   - chunk IDs
   - similarity scores
   - TF-IDF
   - retrieval
   - knowledge bases

6. Rewrite the wording naturally.

7. The presentation MUST be visibly different from the
   original offline answer.

8. Start the response with exactly:

LLM-polished response:

9. Put each technical step on its own bullet line using "•".

10. Do NOT use numbered steps.

11. Keep the response concise.

12. Return only the polished response.


USER QUESTION:
{question}


DETECTED INTENT:
{intent}


DETECTED COMPONENT:
{component}


OFFLINE ANSWER:
{original_answer}
""".strip()

    # ---------------------------------------------------------
    # 5. Call Groq
    # ---------------------------------------------------------

    try:
        client = Groq(
            api_key=api_key
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.6,
            max_tokens=350,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a controlled rewriting layer for an "
                        "evidence-grounded wind turbine maintenance "
                        "advisor. The offline advisor is the technical "
                        "source of truth. Improve presentation only. "
                        "Never add new technical information."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

    except Exception as exc:
        raise RuntimeError(
            f"Groq request failed: {exc}"
        ) from exc

    # ---------------------------------------------------------
    # 6. Read response
    # ---------------------------------------------------------

    improved = response.choices[0].message.content

    if not improved or not improved.strip():
        raise RuntimeError(
            "The LLM returned an empty answer."
        )

    improved = improved.strip()

    print("GROQ API RESPONSE RECEIVED")

    return improved