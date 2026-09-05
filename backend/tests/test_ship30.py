from app.rag.ship30 import validate_ship30


def make_valid_plan():
    return "\n\n".join(
        [
            f"## Day {day}\n- Complete a practical growth activity."
            for day in range(1, 31)
        ]
    )


def test_valid_ship30_plan():
    content = make_valid_plan()

    assert validate_ship30(content) is True


def test_rejects_grouped_days():
    content = """
**Days 1-5**

- Day 1: Research onboarding
- Day 2: Analyze activation
- Day 3: Interview users
- Day 4: Review friction
- Day 5: Improve onboarding
"""

    assert validate_ship30(content) is False


def test_rejects_day_31():
    content = make_valid_plan()

    content += "\n\n## Day 31\n- Extra activity."

    assert validate_ship30(content) is False


def test_rejects_missing_day():
    content = "\n\n".join(
        [
            f"## Day {day}\n- Activity."
            for day in range(1, 30)
        ]
    )

    assert validate_ship30(content) is False


def test_rejects_duplicate_day():
    content = make_valid_plan()

    content += "\n\n## Day 30\n- Duplicate activity."

    assert validate_ship30(content) is False