"""Request validation shared by the resource clients.

Dates retain their local-date or timestamp meaning. Business rules involving the
account timezone, current balances, permissions and card state remain server-side.
"""

import re
from datetime import date, datetime
from typing import Any

from .models import Period, Terminator


def resource_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", value):
        raise ValueError("Resource ID must be a single identifier")
    return value


def integer(value, name, minimum=None, maximum=None):
    if (
        type(value) is not int
        or (minimum is not None and value < minimum)
        or (maximum is not None and value > maximum)
    ):
        raise ValueError(f"Invalid {name}")
    return value


def pagination(page=None, per_page=None, *, first_page=0):
    if page is not None:
        integer(page, "page", first_page)
    if per_page is not None:
        integer(per_page, "page size", 1)


def text_field(value, name, *, required=True, maximum=255):
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > maximum:
        raise ValueError(f"Invalid {name}")
    return value


def date_or_timestamp(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected a date or timestamp string")
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            date.fromisoformat(value)
        elif re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:?\d{2})", value
        ):
            datetime.fromisoformat(value)
        else:
            raise ValueError
    except ValueError:
        raise ValueError("Expected YYYY-MM-DD or an ISO timestamp with timezone") from None
    return value


def validate_recurrence_data(
    balance_cents: int,
    period: str,
    interval: int,
    terminator: str,
    count=None,
    until=None,
    by_week_day=None,
    by_month_day=None,
    by_year_day=None,
    reset_count=None,
) -> dict:
    period = Period(period)
    terminator = Terminator(terminator)
    data = {
        "balanceCents": integer(balance_cents, "balanceCents", 100, 2_100_000_000),
        "period": period.value,
        "interval": integer(interval, "interval", 1),
        "terminator": terminator.value,
    }
    needs_count = terminator in {Terminator.COUNT, Terminator.COUNT_OR_DATE}
    needs_until = terminator in {Terminator.DATE, Terminator.COUNT_OR_DATE}
    if needs_count:
        data["count"] = integer(count, "count", 1)
    elif count is not None:
        raise ValueError("count is not allowed for this terminator")
    if needs_until:
        data["until"] = date_or_timestamp(until)
    elif until is not None:
        raise ValueError("until is not allowed for this terminator")
    selectors = {
        Period.WEEKLY: ("byWeekDay", by_week_day, 0, 6),
        Period.MONTHLY: ("byMonthDay", by_month_day, 1, 31),
        Period.YEARLY: ("byYearDay", by_year_day, 1, 365),
    }
    for selector_period, (name, value, minimum, maximum) in selectors.items():
        if period == selector_period:
            data[name] = integer(value, name, minimum, maximum)
        elif value is not None:
            raise ValueError(f"{name} is not allowed for this period")
    if period == Period.YEARLY and interval != 1:
        raise ValueError("YEARLY recurrence requires interval 1")
    if reset_count is not None:
        if type(reset_count) is not bool:
            raise ValueError("resetCount must be a boolean")
        data["resetCount"] = reset_count
    return data


def _recurrence(config: dict) -> dict:
    if not isinstance(config, dict):
        raise ValueError("recurrence must be an object")
    aliases = {
        "balanceCents": "balance_cents",
        "byWeekDay": "by_week_day",
        "byMonthDay": "by_month_day",
        "byYearDay": "by_year_day",
        "resetCount": "reset_count",
    }
    normalized = {}
    for key, value in config.items():
        key = aliases.get(key, key)
        if key in normalized:
            raise ValueError("Duplicate recurrence field aliases")
        normalized[key] = value
    try:
        return validate_recurrence_data(**normalized)
    except TypeError:
        raise ValueError("Missing or unsupported recurrence fields") from None


def validate_card_update_data(
    balance_cents: int,
    display_name: str | None = None,
    notes: str | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> dict[str, Any]:
    data = {
        "balanceCents": integer(balance_cents, "balanceCents", 100, 2_100_000_000),
        "displayName": text_field(display_name, "displayName"),
    }
    for key, value in (("validFrom", valid_from), ("validTo", valid_to)):
        if value is not None:
            data[key] = date_or_timestamp(value)
    if notes is not None:
        if not isinstance(notes, str):
            raise ValueError("notes must be a string")
        data["notes"] = notes
    return data


def validate_card_creation_data(
    credit_card_id: str,
    display_name: str,
    balance_cents: int,
    recipient_email=None,
    valid_from=None,
    valid_to=None,
    notes=None,
    recurs=None,
    recurrence=None,
) -> dict:
    data = validate_card_update_data(balance_cents, display_name, notes, valid_from, valid_to)
    data["creditCardId"] = resource_id(credit_card_id)
    if recipient_email is not None:
        data["recipient"] = recipient_email
    if recurs is not None:
        if type(recurs) is not bool:
            raise ValueError("recurs must be a boolean")
        data["recurs"] = recurs
    if recurs is True:
        if recurrence is None:
            raise ValueError("Recurring cards require recurrence")
        data["recurrence"] = _recurrence(recurrence)
    elif recurrence is not None:
        raise ValueError("recurrence requires recurs=True")
    return data


def validate_card_data(
    credit_card_id: str, display_name: str, balance_cents: int, **kwargs
) -> dict:
    """Legacy camelCase payload helper; use resource methods for card operations."""
    data = validate_card_creation_data(credit_card_id, display_name, balance_cents)
    data.update({key: value for key, value in kwargs.items() if value is not None})
    return data
