"""Offline wind-turbine operation and maintenance advisor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1. Paths and Data Loading
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge_base.json"
CHUNKS_PATH = DATA_DIR / "chunks.json"


def load_json(path: Path) -> Any:
    """Load a required JSON file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required file was not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


knowledge_base = load_json(KNOWLEDGE_BASE_PATH)
chunks = load_json(CHUNKS_PATH)


# ============================================================
# 2. TF-IDF Retrieval Setup
# ============================================================

if not chunks:
    raise ValueError("chunks.json is empty.")

chunk_texts = [
    chunk.get("text", "")
    for chunk in chunks
]

vectorizer = TfidfVectorizer(
    stop_words="english"
)

chunk_vectors = vectorizer.fit_transform(chunk_texts)


# ============================================================
# 3. Text Normalization
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize text for rule matching."""
    if not text:
        return ""

    return (
        text.lower()
        .strip()
        .replace("-", " ")
        .replace("_", " ")
    )


# ============================================================
# 4. Component Alias Index
# ============================================================

def build_alias_index(kb: dict[str, Any]) -> dict[str, str]:
    """Map component names and aliases to canonical component names."""
    index: dict[str, str] = {}

    for component, info in kb.items():
        normalized_component = normalize_text(component)
        index[normalized_component] = component

        for alias in info.get("aliases", []):
            normalized_alias = normalize_text(alias)

            if normalized_alias:
                index[normalized_alias] = component

    return index


alias_index = build_alias_index(knowledge_base)


# ============================================================
# 5. Component Detection
# ============================================================

def detect_component(question: str) -> str:
    """Detect a named turbine component."""
    normalized_question = normalize_text(question)

    sorted_aliases = sorted(
        alias_index.keys(),
        key=len,
        reverse=True,
    )

    for alias in sorted_aliases:
        if alias in normalized_question:
            return alias_index[alias]

    return "unknown"


# ============================================================
# 6. General Manual Topic Detection
# ============================================================

def detect_general_topic(question: str) -> str | None:
    """
    Detect important manual topics that do not require the user
    to name one specific component.
    """
    normalized_question = normalize_text(question)

    if any(
        phrase in normalized_question
        for phrase in (
            "short circuit",
            "shortcircuit",
            "shorted",
        )
    ):
        return "short_circuit"

    if any(
        phrase in normalized_question
        for phrase in (
            "safety equipment",
            "protective equipment",
            "personal protective equipment",
            "what should i wear",
            "what to wear",
            "ppe",
        )
    ):
        return "safety_equipment"

    if any(
        phrase in normalized_question
        for phrase in (
            "rust",
            "rusted",
            "rusty",
            "corrosion",
            "corroded",
        )
    ):
        return "rust"

    return None


GENERAL_TOPIC_COMPONENTS = {
    "rust": "metal parts and cables",
    "safety_equipment": "general safety",
    "short_circuit": "electrical system",
}


# ============================================================
# 7. Intent Detection
# ============================================================

intent_keywords = {
    "maintenance": [
        "maintain",
        "maintenance",
        "repair",
        "replace",
        "service",
        "fix",
    ],
    "inspection": [
        "inspect",
        "inspection",
        "check",
        "examine",
        "look at",
    ],
    "safety": [
        "risk",
        "risks",
        "danger",
        "warning",
        "safe",
        "safety",
        "hazard",
        "wear",
        "ppe",
        "protective equipment",
        "safety equipment",
    ],
    "troubleshooting": [
        "problem",
        "issue",
        "broken",
        "rust",
        "rusty",
        "corrosion",
        "corroded",
        "short circuit",
        "shortcircuit",
        "not working",
        "fault",
        "failure",
    ],
    "tools_materials": [
        "tool",
        "tools",
        "material",
        "materials",
        "equipment",
        "need",
        "use",
    ],
}


def detect_intent(
    question: str,
    general_topic: str | None = None,
) -> str:
    """Detect the question intent."""
    if general_topic == "safety_equipment":
        return "safety"

    if general_topic in {"rust", "short_circuit"}:
        return "troubleshooting"

    normalized_question = normalize_text(question)

    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if normalize_text(keyword) in normalized_question:
                return intent

    return "general"


# ============================================================
# 8. Manual Chunk Retrieval
# ============================================================

GENERAL_TOPIC_RETRIEVAL_QUERIES = {
    "rust": (
        "rust cable clamps guy wires metal frame tower "
        "grease used motor oil broken cable strand"
    ),
    "safety_equipment": (
        "safety gear gloves safety shoes safety helmet "
        "maintenance safety precautions"
    ),
    "short_circuit": (
        "short circuit tower wire alternator wiring rectifier "
        "controller electrical shock battery explosion"
    ),
}


def retrieve_chunks(
    question: str,
    top_k: int = 3,
    general_topic: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve the most relevant manual chunks using TF-IDF."""
    if not question.strip():
        return []

    retrieval_query = question

    if general_topic in GENERAL_TOPIC_RETRIEVAL_QUERIES:
        retrieval_query = (
            f"{question} "
            f"{GENERAL_TOPIC_RETRIEVAL_QUERIES[general_topic]}"
        )

    question_vector = vectorizer.transform([retrieval_query])

    similarities = cosine_similarity(
        question_vector,
        chunk_vectors,
    )[0]

    top_k = min(top_k, len(chunks))
    top_indices = similarities.argsort()[::-1][:top_k]

    results: list[dict[str, Any]] = []

    for idx in top_indices:
        chunk = chunks[idx]

        results.append(
            {
                "chunk_id": chunk.get(
                    "chunk_id",
                    str(idx),
                ),
                "score": float(similarities[idx]),
                "text": chunk.get("text", ""),
            }
        )

    return results


# ============================================================
# 9. Confidence Calculation
# ============================================================

def compute_confidence(
    component: str,
    kb_info: dict[str, Any] | None,
    retrieved_chunks: list[dict[str, Any]],
    general_topic: str | None = None,
) -> str:
    """Calculate a simple high, medium, or low confidence value."""
    best_score = (
        retrieved_chunks[0].get("score", 0.0)
        if retrieved_chunks
        else 0.0
    )

    if general_topic:
        if best_score >= 0.20:
            return "high"

        if best_score >= 0.10:
            return "medium"

        return "low"

    if component == "unknown" or kb_info is None:
        return "low"

    if best_score >= 0.20:
        return "high"

    if best_score >= 0.10:
        return "medium"

    return "low"


# ============================================================
# 10. Safety Topic Detection
# ============================================================

safety_keywords = {
    "electrical": [
        "electric",
        "electrical",
        "electricity",
        "voltage",
        "current",
        "shock",
        "short circuit",
        "shortcircuit",
        "power cable",
        "inverter",
        "battery",
    ],
    "mechanical": [
        "mechanical",
        "moving parts",
        "rotor",
        "blade",
        "bearing",
        "brake",
        "rotation",
    ],
    "height": [
        "height",
        "tower",
        "mast",
        "climb",
        "climbing",
        "fall",
        "lowering the tower",
        "raising the tower",
    ],
    "magnets": [
        "magnet",
        "magnets",
        "magnetic",
    ],
    "weather": [
        "lightning",
        "storm",
        "rain",
        "wind",
        "weather",
    ],
    "personal_protective_equipment": [
        "ppe",
        "protective equipment",
        "safety equipment",
        "gloves",
        "helmet",
        "safety shoes",
        "what should i wear",
    ],
}


def detect_safety_topics(question: str) -> list[str]:
    """Detect safety topics mentioned in the question."""
    normalized_question = normalize_text(question)
    detected_topics: list[str] = []

    for topic, keywords in safety_keywords.items():
        for keyword in keywords:
            if normalize_text(keyword) in normalized_question:
                detected_topics.append(topic)
                break

    return detected_topics


# ============================================================
# 11. Safety Warnings
# ============================================================

GENERAL_TOPIC_WARNINGS = {
    "rust": [
        (
            "Replace the cable if any cable strand is broken; "
            "surface protection is not enough for damaged cable."
        ),
    ],
    "safety_equipment": [
        (
            "Safety must remain the primary concern during all "
            "maintenance operations."
        ),
        (
            "Be attentive to both electrical and mechanical risks."
        ),
    ],
    "short_circuit": [
        (
            "Live electrical wires can create a risk of electric shock."
        ),
        (
            "A short circuit in battery wiring can cause burning "
            "or an explosion."
        ),
        (
            "Avoid sparks, flames, and other ignition sources near "
            "lead-acid batteries."
        ),
    ],
}


def collect_safety_warnings(
    component: str,
    question: str,
    general_topic: str | None = None,
) -> list[str]:
    """Collect grounded safety warnings."""
    collected_warnings: list[str] = []

    if general_topic in GENERAL_TOPIC_WARNINGS:
        collected_warnings.extend(
            GENERAL_TOPIC_WARNINGS[general_topic]
        )

    normalized_question = normalize_text(question)

    if component != "unknown":
        kb_info = knowledge_base.get(component)

        if kb_info:
            for warning in kb_info.get("safety_warnings", []):
                if warning not in collected_warnings:
                    collected_warnings.append(warning)

    question_words = set(normalized_question.split())

    ignored_words = {
        "what",
        "should",
        "do",
        "i",
        "the",
        "a",
        "an",
        "are",
        "is",
        "in",
        "of",
        "for",
        "with",
        "when",
        "case",
        "needed",
        "any",
        "to",
        "before",
        "during",
        "about",
        "how",
        "can",
        "my",
    }

    meaningful_question_words = question_words - ignored_words

    for _, info in knowledge_base.items():
        warnings = info.get("safety_warnings", [])

        for warning in warnings:
            normalized_warning = normalize_text(warning)
            warning_words = set(normalized_warning.split())

            if (
                "short circuit" in normalized_question
                and "short circuit brake" in normalized_warning
                and component != "brake"
            ):
                continue

            overlap = meaningful_question_words.intersection(
                warning_words
            )

            if overlap and warning not in collected_warnings:
                collected_warnings.append(warning)

    return collected_warnings


# ============================================================
# 12. Knowledge-Base Helpers
# ============================================================

def get_list_field(
    kb_info: dict[str, Any] | None,
    possible_keys: list[str],
) -> list[str]:
    """Read the first available list field."""
    if not kb_info:
        return []

    for key in possible_keys:
        value = kb_info.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, str) and value.strip():
            return [value.strip()]

    return []


def get_text_field(
    kb_info: dict[str, Any] | None,
    possible_keys: list[str],
) -> str:
    """Read the first available text field."""
    if not kb_info:
        return ""

    for key in possible_keys:
        value = kb_info.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def number_steps(steps: list[str]) -> str:
    """Convert instructions into numbered lines."""
    return "\n".join(
        f"{index}. {step}"
        for index, step in enumerate(steps, start=1)
    )


# ============================================================
# 13. General Topic Answers
# ============================================================

GENERAL_TOPIC_ANSWERS = {
    "rust": [
        (
            "Inspect the rusty part and determine whether the rust "
            "is on cable clamps, guy wires, the tower, or another "
            "metal part."
        ),
        "Protect rusty cable clamps with grease.",
        (
            "Guy wires with rust can be protected with used motor oil."
        ),
        (
            "Replace the cable if you find a broken cable strand."
        ),
        (
            "Check the tower and metal frame for rust and cracks "
            "in the welds."
        ),
    ],
    "safety_equipment": [
        "Wear protective gloves.",
        "Wear safety shoes.",
        "Wear a safety helmet.",
        (
            "Work carefully and make sure everyone nearby behaves "
            "responsibly."
        ),
    ],
    "short_circuit": [
        (
            "Disconnect the tower wire to help locate the short circuit."
        ),
        (
            "If the turbine still does not start, the short circuit "
            "may be in the tower cable or alternator."
        ),
        (
            "If the turbine starts, check the other wiring, rectifier, "
            "or controller."
        ),
        (
            "If an alternator winding failure is suspected, lower the "
            "turbine and check the stator voltage output."
        ),
    ],
}


GENERAL_TOPIC_TOOLS = {
    "rust": [
        "grease",
        "used motor oil",
    ],
    "safety_equipment": [
        "protective gloves",
        "safety shoes",
        "safety helmet",
    ],
    "short_circuit": [
        "appropriate electrical testing equipment",
    ],
}


def build_general_topic_answer(
    general_topic: str,
) -> str:
    """Build a grounded answer for a general manual topic."""
    steps = GENERAL_TOPIC_ANSWERS.get(general_topic, [])

    if not steps:
        return (
            "The manual does not contain enough structured "
            "information to answer this question."
        )

    return number_steps(steps)


# ============================================================
# 14. Component-Based Offline Answer
# ============================================================

def build_component_answer(
    component: str,
    intent: str,
    kb_info: dict[str, Any] | None,
    evidence: list[dict[str, Any]],
) -> str:
    """Build an answer from one detected knowledge-base component."""
    if component == "unknown" or kb_info is None:
        if evidence and evidence[0].get("score", 0) > 0:
            return (
                "I could not identify a specific turbine component "
                "from the question. Please mention the component, "
                "such as the battery, tower, blades, inverter, "
                "brake, or cable."
            )

        return (
            "I could not find enough information to answer the "
            "question. Please mention the turbine component and "
            "the type of help you need."
        )

    maintenance_steps = get_list_field(
        kb_info,
        [
            "maintenance_steps",
            "maintenance",
            "maintenance_actions",
            "procedures",
        ],
    )

    inspection_steps = get_list_field(
        kb_info,
        [
            "inspection_steps",
            "inspection",
            "checks",
            "checklist",
        ],
    )

    troubleshooting_steps = get_list_field(
        kb_info,
        [
            "troubleshooting",
            "troubleshooting_steps",
            "problems",
            "faults",
        ],
    )

    description = get_text_field(
        kb_info,
        [
            "description",
            "overview",
            "summary",
        ],
    )

    if intent == "maintenance" and maintenance_steps:
        return number_steps(maintenance_steps)

    if intent == "inspection" and inspection_steps:
        return number_steps(inspection_steps)

    if (
        intent == "troubleshooting"
        and troubleshooting_steps
    ):
        return number_steps(troubleshooting_steps)

    if description:
        return description

    if maintenance_steps:
        return number_steps(maintenance_steps)

    if inspection_steps:
        return number_steps(inspection_steps)

    if evidence:
        return evidence[0].get(
            "text",
            "No readable evidence text was found.",
        )

    return (
        f"The component '{component}' was detected, but no "
        "detailed answer was found in the knowledge base."
    )


# ============================================================
# 15. Main Offline Function
# ============================================================

def generate_offline_answer(question: str) -> dict[str, Any]:
    """Generate the complete grounded offline advisor result."""
    if not question or not question.strip():
        raise ValueError("The question cannot be empty.")

    general_topic = detect_general_topic(question)
    detected_component = detect_component(question)

    if general_topic:
        component = GENERAL_TOPIC_COMPONENTS[general_topic]
    else:
        component = detected_component

    intent = detect_intent(
        question,
        general_topic=general_topic,
    )

    kb_info = (
        knowledge_base.get(detected_component)
        if detected_component != "unknown"
        else None
    )

    evidence = retrieve_chunks(
        question,
        top_k=3,
        general_topic=general_topic,
    )

    confidence = compute_confidence(
        component=detected_component,
        kb_info=kb_info,
        retrieved_chunks=evidence,
        general_topic=general_topic,
    )

    safety_topics = detect_safety_topics(question)

    safety_warnings = collect_safety_warnings(
        component=detected_component,
        question=question,
        general_topic=general_topic,
    )

    if general_topic:
        tools_materials = GENERAL_TOPIC_TOOLS.get(
            general_topic,
            [],
        )

        answer = build_general_topic_answer(
            general_topic
        )
    else:
        tools_materials = get_list_field(
            kb_info,
            [
                "tools_materials",
                "tools_and_materials",
                "tools",
                "materials",
                "equipment",
            ],
        )

        answer = build_component_answer(
            component=detected_component,
            intent=intent,
            kb_info=kb_info,
            evidence=evidence,
        )

    return {
        "question": question,
        "intent": intent,
        "component": component,
        "confidence": confidence,
        "answer": answer,
        "tools_materials": tools_materials,
        "safety_topics": safety_topics,
        "safety_warnings": safety_warnings,
        "evidence": evidence,
    }


# ============================================================
# 16. Local Test
# ============================================================

if __name__ == "__main__":
    test_question = "What should I do in case of short circuit?"

    result = generate_offline_answer(test_question)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )