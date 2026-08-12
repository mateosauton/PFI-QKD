"""Validation rules for assistant feedback stored by the study app."""

from __future__ import annotations

from typing import Any

from .catalog import CAPABILITIES


STATUSES = ("red", "yellow", "green", "blue")
NEXT_ACTIONS = ("advance", "recovery", "review")


def validate_feedback(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["feedback must be an object"]
    if not isinstance(value.get("attempt_id"), str) or not value["attempt_id"].strip():
        errors.append("attempt_id is required")
    criteria = value.get("criteria")
    if not isinstance(criteria, dict):
        errors.append("criteria is required")
        criteria = {}
    for capability in CAPABILITIES:
        item = criteria.get(capability)
        if not isinstance(item, dict):
            errors.append(f"criteria.{capability} is required")
            continue
        if item.get("status") not in STATUSES:
            errors.append(f"criteria.{capability}.status must be one of {', '.join(STATUSES)}")
        if not isinstance(item.get("note"), str) or not item["note"].strip():
            errors.append(f"criteria.{capability}.note is required")
    for field in ("strengths", "errors"):
        if not isinstance(value.get(field), list) or not all(isinstance(item, str) and item.strip() for item in value[field]):
            errors.append(f"{field} must be a list of non-empty strings")
    if value.get("next_action") not in NEXT_ACTIONS:
        errors.append(f"next_action must be one of {', '.join(NEXT_ACTIONS)}")
    hint = value.get("hint")
    if not isinstance(hint, dict) or not isinstance(hint.get("text"), str) or not hint["text"].strip():
        errors.append("hint.text is required")
    elif hint.get("level") not in (1, 2, 3):
        errors.append("hint.level must be 1, 2 or 3")
    return errors
