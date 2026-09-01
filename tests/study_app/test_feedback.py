from study_app.catalog import CAPABILITIES
from study_app.feedback_schema import validate_feedback


def valid_feedback():
    return {
        "attempt_id": "attempt-1",
        "criteria": {capability: {"status": "green", "note": "evidencia"} for capability in CAPABILITIES},
        "strengths": ["mecanismo correcto"],
        "errors": [],
        "next_action": "advance",
        "hint": {"level": 1, "text": "seguí conectando con QBER"},
    }


def test_feedback_requires_all_four_capabilities():
    feedback = valid_feedback()
    assert validate_feedback(feedback) == []
    del feedback["criteria"]["defend"]
    assert "criteria.defend is required" in validate_feedback(feedback)


def test_feedback_rejects_unknown_next_action():
    feedback = valid_feedback()
    feedback["next_action"] = "guess"
    assert "next_action must be one of" in validate_feedback(feedback)[0]


def test_feedback_rejects_invalid_status_and_empty_note():
    feedback = valid_feedback()
    feedback["criteria"]["calculate"] = {"status": "purple", "note": ""}
    errors = validate_feedback(feedback)
    assert "criteria.calculate.status must be one of" in errors[0]
    assert "criteria.calculate.note is required" in errors[1]
