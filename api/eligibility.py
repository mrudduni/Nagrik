"""
api/eligibility.py
------------------
Deterministic Python evaluation of EligibilityRule nodes against
a citizen's profile. No LLM is called here.

Each rule has:
  field    – snake_case name matching CitizenProfile fields
  operator – one of: eq, ne, lt, lte, gt, gte, in, not_in, contains
  value    – string representation of the target value
"""

from __future__ import annotations

import re
from typing import Any
from api.models import CitizenProfile, RuleEvaluation

VALID_OPERATORS = {"eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in", "contains"}

FIELD_ALIASES = {
    "residence_state": "state",
    "caste": "category",
    "caste_category": "category",
    "social_category": "category",
    "annual_income": "income_annual",
    "family_income": "income_annual",
    "household_income": "income_annual",
    "income": "income_annual",
    "sex": "gender",
    "pwd": "disability",
    "physically_handicapped": "disability",
}


def _extract_number(val: Any) -> float | None:
    """Safely extracts a numeric float from various string formats (e.g. '₹ 1,00,000')."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = str(val).replace(",", "").replace("₹", "").replace("INR", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def _split_options(raw_val: Any) -> list[str]:
    """Splits multiple rule options by pipe, comma, or slash."""
    s = str(raw_val).strip()
    # Split by | or comma or /
    parts = re.split(r"[,|/]+", s)
    return [p.strip().lower() for p in parts if p.strip()]


def evaluate_rule(
    rule: dict,
    profile: CitizenProfile,
) -> RuleEvaluation:
    """
    Evaluate a single EligibilityRule against a CitizenProfile safely.
    Returns RuleEvaluation with status = 'passed' | 'failed' | 'uncertain'.
    """
    try:
        field: str = str(rule.get("field", "")).strip().lower()
        operator: str = str(rule.get("operator", "eq")).strip().lower()
        rule_value: str = str(rule.get("value", "")).strip()

        if not field:
            return RuleEvaluation(
                field="unknown",
                operator=operator,
                value=rule_value,
                status="uncertain",
                reason="Rule has empty field",
            )

        # Map field to profile attribute
        profile_dict = profile.model_dump()
        mapped_field = FIELD_ALIASES.get(field, field)
        citizen_val = profile_dict.get(mapped_field)

        if citizen_val is None:
            return RuleEvaluation(
                field=field,
                operator=operator,
                value=rule_value,
                status="uncertain",
                reason=f"Citizen profile does not provide '{field}'",
            )

        if operator not in VALID_OPERATORS:
            return RuleEvaluation(
                field=field,
                operator=operator,
                value=rule_value,
                status="uncertain",
                reason=f"Unknown operator '{operator}'",
            )

        # Evaluate based on operator
        ok = False

        if operator in ("lt", "lte", "gt", "gte"):
            c_num = _extract_number(citizen_val)
            r_num = _extract_number(rule_value)
            if c_num is None or r_num is None:
                return RuleEvaluation(
                    field=field,
                    operator=operator,
                    value=rule_value,
                    status="uncertain",
                    reason=f"Cannot compare non-numeric values ({citizen_val} vs {rule_value})",
                )
            if operator == "lt":
                ok = c_num < r_num
            elif operator == "lte":
                ok = c_num <= r_num
            elif operator == "gt":
                ok = c_num > r_num
            elif operator == "gte":
                ok = c_num >= r_num

        elif operator == "eq":
            if isinstance(citizen_val, bool):
                r_bool = rule_value.lower() in ("true", "yes", "1", "applicable", "required")
                ok = citizen_val == r_bool
            else:
                ok = str(citizen_val).strip().lower() == rule_value.strip().lower()

        elif operator == "ne":
            if isinstance(citizen_val, bool):
                r_bool = rule_value.lower() in ("true", "yes", "1", "applicable", "required")
                ok = citizen_val != r_bool
            else:
                ok = str(citizen_val).strip().lower() != rule_value.strip().lower()

        elif operator in ("in", "contains"):
            options = _split_options(rule_value)
            c_str = str(citizen_val).strip().lower()
            ok = any(opt == c_str or opt in c_str or c_str in opt for opt in options)

        elif operator == "not_in":
            options = _split_options(rule_value)
            c_str = str(citizen_val).strip().lower()
            ok = not any(opt == c_str or opt in c_str or c_str in opt for opt in options)

        return RuleEvaluation(
            field=field,
            operator=operator,
            value=rule_value,
            status="passed" if ok else "failed",
            reason=None if ok else f"Value '{citizen_val}' did not satisfy '{operator} {rule_value}'",
        )

    except Exception as e:
        return RuleEvaluation(
            field=str(rule.get("field", "unknown")),
            operator=str(rule.get("operator", "unknown")),
            value=str(rule.get("value", "")),
            status="uncertain",
            reason=f"Evaluation error: {e}",
        )


def evaluate_eligibility(
    rules: list[dict],
    profile: CitizenProfile,
) -> tuple[str, list[RuleEvaluation]]:
    """
    Evaluate all rules for a scheme.

    Returns:
        (status, evaluations)
        status: 'Eligible' | 'Not Eligible' | 'Uncertain'
    """
    if not rules:
        return "Uncertain", []

    evaluations = [evaluate_rule(r, profile) for r in rules if isinstance(r, dict) and r.get("field")]

    if not evaluations:
        return "Uncertain", []

    # If any rule explicitly FAILS → Not Eligible
    if any(e.status == "failed" for e in evaluations):
        return "Not Eligible", evaluations

    # If all rules pass → Eligible
    if all(e.status == "passed" for e in evaluations):
        return "Eligible", evaluations

    # Mixed passed + uncertain → Uncertain
    return "Uncertain", evaluations
