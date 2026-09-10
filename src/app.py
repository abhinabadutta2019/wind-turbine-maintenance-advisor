"""Command-line application for the maintenance advisor."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from advisor import generate_offline_answer
from llm_answer import improve_answer_with_llm


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Wind Turbine Operation and Maintenance Advisor."
    )

    parser.add_argument(
        "question",
        help="Maintenance or safety question to ask.",
    )

    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Optionally improve the offline answer wording with Groq/Llama.",
    )

    return parser.parse_args()


def print_value(title: str, value: Any) -> None:
    """Print one output section in a readable format."""
    print(f"\n{title}:")

    if value is None or value == "" or value == []:
        print("- No information available in the manual.")
        return

    if isinstance(value, list):
        for item in value:
            print(f"- {item}")
        return

    if isinstance(value, str) and "\n" in value:
        for line in value.splitlines():
            clean_line = line.strip()

            if clean_line:
                print(clean_line)
        return

    print(value)


def print_evidence(evidence: Any) -> None:
    """Print the retrieved manual evidence chunks."""
    print("\nEvidence from manual:")

    if not evidence:
        print("- No supporting evidence chunk was found.")
        return

    for item in evidence:
        if not isinstance(item, dict):
            print(f"- {item}")
            continue

        chunk_id = item.get("chunk_id", "unknown")
        score = item.get("score")
        text = item.get("text", "")

        evidence_line = f"- chunk_id: {chunk_id}"

        if score is not None:
            try:
                evidence_line += f" | score: {float(score):.3f}"
            except (TypeError, ValueError):
                evidence_line += f" | score: {score}"

        print(evidence_line)

        if text:
            cleaned_text = " ".join(str(text).split())
            print(f"  {cleaned_text}")


def print_result(result: dict[str, Any]) -> None:
    """Print the final advisor result using the required structure."""
    print_value("Question", result.get("question"))
    print_value("Detected intent", result.get("intent"))
    print_value("Detected component", result.get("component"))
    print_value("Confidence", result.get("confidence"))
    print_value("Answer", result.get("answer"))
    print_value("Tools/materials", result.get("tools_materials"))
    print_value("Safety warnings", result.get("safety_warnings"))
    print_evidence(result.get("evidence"))

    print_value("Answer mode", result.get("answer_mode"))

    if result.get("llm_warning"):
        print_value("LLM warning", result.get("llm_warning"))


def main() -> int:
    """Run the command-line advisor."""
    args = parse_arguments()

    try:
        result = generate_offline_answer(args.question)
    except Exception as exc:
        print(f"Advisor error: {exc}", file=sys.stderr)
        return 1

    result["answer_mode"] = "offline_advisor"

    if args.use_llm:
        try:
            improved_answer = improve_answer_with_llm(
                question=args.question,
                advisor_result=result,
            )

            if improved_answer:
                result["answer"] = improved_answer
                result["answer_mode"] = (
                    "offline_advisor_with_llm_rewriting"
                )

        except Exception as exc:
            result["answer_mode"] = "offline_advisor"
            result["llm_warning"] = str(exc)

    print_result(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())