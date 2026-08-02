from src.advisor import generate_offline_answer


def test_tower_inspection() -> None:
    result = generate_offline_answer(
        "How should I inspect the tower?"
    )

    assert result["intent"] == "inspection"
    assert result["component"] == "tower"
    assert result["answer"]
    assert result["evidence"]


def test_battery_maintenance() -> None:
    result = generate_offline_answer(
        "How do I maintain the battery?"
    )

    assert result["component"] == "battery"
    assert result["answer"]


def test_safety_information_exists() -> None:
    result = generate_offline_answer(
        "What safety precautions are needed for the tower?"
    )

    assert "safety_topics" in result
    assert "safety_warnings" in result