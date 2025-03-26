from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .models import (
    RecurrenceConfig,
    CardCreationRequest,
    Period,
    Terminator
)


def validate_card_creation_data(
        credit_card_id: str,
        display_name: str,
        balance_cents: int,
        recipient_email: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
        notes: Optional[str] = None,
        recurs: bool = False,
        recurrence: Optional[Dict] = None,
) -> CardCreationRequest:
    """Validate and format card creation data.

    Args:
        credit_card_id (str): ID of the parent credit card
        display_name (str): Name to display for the virtual card
        balance_cents (int): Initial balance in cents
        recipient_email (Optional[str]): Email of the card recipient
        valid_from (Optional[str]): Start date in YYYY-MM-DD format
        valid_to (Optional[str]): Expiration date in YYYY-MM-DD format
        notes (Optional[str]): Additional notes about the card
        recurs (bool): Flag to indicate the card should recur
        recurrence (Optional[Dict]): Recurrence configuration

    Returns:
        CardCreationRequest: Validated and formatted card creation data

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    if not credit_card_id:
        raise ValueError("Credit card ID is required")

    if balance_cents <= 0:
        raise ValueError("Balance must be greater than 0")

    if not display_name:
        raise ValueError("Display name is required")

    # Build the result dictionary with camelCase keys.
    data: CardCreationRequest = {
        "creditCardId": credit_card_id,
        "displayName": display_name,
        "balanceCents": balance_cents,
    }

    if recipient_email:
        # Basic email format validation
        if "@" not in recipient_email or "." not in recipient_email:
            raise ValueError("Invalid email format")
        data["recipient"] = recipient_email

    if valid_from:
        try:
            # Validate date format and ensure it's not in the past
            valid_from_date = datetime.strptime(valid_from, "%Y-%m-%d")
            if valid_from_date.date() < datetime.now().date():
                raise ValueError("validFrom date cannot be in the past")
            data["validFrom"] = f"{valid_from}T00:00:00.000Z"
        except ValueError as e:
            if "strptime" in str(e):
                raise ValueError("validFrom must be in YYYY-MM-DD format")
            raise

    if valid_to:
        try:
            # Handle both simple date format and ISO format with time
            if "T" in valid_to:
                valid_to_date = datetime.strptime(valid_to.split("T")[0], "%Y-%m-%d")
            else:
                valid_to_date = datetime.strptime(valid_to, "%Y-%m-%d")

            if valid_from:
                if "T" in valid_from:
                    valid_from_date = datetime.strptime(valid_from.split("T")[0], "%Y-%m-%d")
                else:
                    valid_from_date = datetime.strptime(valid_from, "%Y-%m-%d")
                if valid_to_date.date() <= valid_from_date.date():
                    raise ValueError("validTo must be after validFrom")
            data["validTo"] = valid_to if "T" in valid_to else f"{valid_to}T23:59:59.999Z"
        except ValueError as e:
            if "strptime" in str(e):
                raise ValueError("validTo must be in YYYY-MM-DD format or ISO format with time")
            raise

    if notes:
        if len(notes) > 500:  # Add a reasonable max length
            raise ValueError("Notes must be less than 500 characters")
        data["notes"] = notes

    if recurs:
        if not recurrence:
            raise ValueError("recurrence configuration is required for recurring cards")
        if not all([recurrence["period"], recurrence["interval"], recurrence["terminator"]]):
            raise ValueError("period, interval, and terminator are required for recurring cards")
        else:
            data["recurs"] = True
            data["recurrence"] = validate_recurrence_data(**recurrence)

    return data


def validate_recurrence_data(
        balance_cents: int,
        period: str,
        interval: int,
        terminator: str,
        count: Optional[int] = None,
        until: Optional[str] = None,
        by_week_day: Optional[int] = None,
        by_month_day: Optional[int] = None,
        by_year_day: Optional[int] = None,
) -> RecurrenceConfig:
    """
    Validate and format recurrence configuration data.

    Args:
        balance_cents (int): Balance for each recurring card.
        period (str): Recurrence period ("DAILY", "WEEKLY", "MONTHLY", "YEARLY").
        interval (int): Number of periods between recurrences.
        terminator (str): How to end the recurrence ("NONE", "COUNT", "DATE", "COUNT_OR_DATE").
        count (Optional[int]): Number of recurrences if terminator is "COUNT".
        until (Optional[str]): End date in YYYY-MM-DD format if terminator is "DATE".
        by_week_day (Optional[int]): Day of week (0-6) for weekly recurrence.
        by_month_day (Optional[int]): Day of month (1-31) for monthly recurrence.
        by_year_day (Optional[int]): Day of year (1-366) for yearly recurrence.

    Returns:
        RecurrenceConfig: Validated and formatted recurrence configuration.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Convert period and terminator to enum members.
    try:
        period_enum = Period(period)
    except ValueError:
        valid_periods = [e for e in Period]
        raise ValueError(f"Period must be one of: {', '.join(valid_periods)}")

    try:
        terminator_enum = Terminator(terminator)
    except ValueError:
        valid_terminators = [e for e in Terminator]
        raise ValueError(f"Terminator must be one of: {', '.join(valid_terminators)}")

    if balance_cents <= 0:
        raise ValueError("Recurrence balanceCents must be greater than 0")

    if interval <= 0:
        raise ValueError("Interval must be greater than 0")

    # Build the result dictionary with camelCase keys.
    data: RecurrenceConfig = {
        "balanceCents": balance_cents,
        "period": period_enum.value,
        "interval": interval,
        "terminator": terminator_enum.value,
    }

    # Validate terminator-specific fields.
    if terminator_enum in {Terminator.COUNT, Terminator.COUNT_OR_DATE}:
        if count is None:
            raise ValueError("Count is required for COUNT or COUNT_OR_DATE terminator")
        if count <= 0:
            raise ValueError("Count must be greater than 0")
        data["count"] = count

    if terminator_enum in {Terminator.DATE, Terminator.COUNT_OR_DATE}:
        if not until:
            raise ValueError("Until date is required for DATE or COUNT_OR_DATE terminator")
        try:
            # Handle both simple date format and ISO format with time.
            if "T" in until:
                until_date = datetime.strptime(until.split("T")[0], "%Y-%m-%d")
            else:
                until_date = datetime.strptime(until, "%Y-%m-%d")
            if until_date.date() <= datetime.now().date():
                raise ValueError("Until date must be in the future")
            data["until"] = until if "T" in until else f"{until}T23:59:59.999Z"
        except ValueError as e:
            if "strptime" in str(e):
                raise ValueError("Until date must be in YYYY-MM-DD format or ISO format with time")
            raise

    # Validate period-specific fields.
    if period_enum == Period.WEEKLY:
        if by_week_day is None:
            raise ValueError("byWeekDay is required for WEEKLY period")
        if not 0 <= by_week_day <= 6:
            raise ValueError("byWeekDay must be between 0 and 6 (Monday to Sunday)")
        data["byWeekDay"] = by_week_day

    elif period_enum == Period.MONTHLY:
        if by_month_day is None:
            raise ValueError("byMonthDay is required for MONTHLY period")
        if not 1 <= by_month_day <= 31:
            raise ValueError("byMonthDay must be between 1 and 31")
        # Additional validation for invalid dates like February 31.
        if by_month_day > 28:
            for month in range(1, 13):
                try:
                    datetime(2024, month, by_month_day)  # Using a leap year for February.
                except ValueError:
                    raise ValueError(
                        f"byMonthDay {by_month_day} is invalid as it doesn't exist in all months. "
                        "Choose a day between 1 and 28 for consistent monthly recurrence."
                    )
        data["byMonthDay"] = by_month_day

    elif period_enum == Period.YEARLY:
        if by_year_day is None:
            raise ValueError("byYearDay is required for YEARLY period")
        if not 1 <= by_year_day <= 365:
            raise ValueError("byYearDay must be between 1 and 365")
        try:
            datetime(2023, 1, 1) + timedelta(days=by_year_day - 1)
        except ValueError:
            raise ValueError(
                f"byYearDay {by_year_day} is invalid as it doesn't exist in non-leap years. "
                "Choose a different day for consistent yearly recurrence."
            )
        data["byYearDay"] = by_year_day

    elif period_enum == Period.DAILY:
        if any([by_week_day, by_month_day, by_year_day]):
            raise ValueError("DAILY period should not include byWeekDay, byMonthDay, or byYearDay")

    return data


def validate_card_update_data(
        balance_cents: int,
        display_name: Optional[str] = None,
        notes: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate and format card update data.

    Args:
        balance_cents (int): New balance in cents.
        display_name (Optional[str]): New display name.
        notes (Optional[str]): New notes.
        valid_from (Optional[str]): New start date in YYYY-MM-DD format.
        valid_to (Optional[str]): New expiration date in YYYY-MM-DD format.

    Returns:
        Dict[str, Any]: Formatted update data with camelCase keys for the API payload.

    Raises:
        ValueError: If date formats are invalid or valid_to is not after valid_from.
    """
    update_data: Dict[str, Any] = {
        "balanceCents": balance_cents
    }

    if display_name:
        update_data["displayName"] = display_name

    if notes:
        update_data["notes"] = notes

    if valid_from:
        try:
            # Validate valid_from date format
            datetime.strptime(valid_from, "%Y-%m-%d")
            update_data["validFrom"] = f"{valid_from}T00:00:00.000Z"
        except ValueError:
            raise ValueError("validFrom must be in YYYY-MM-DD format")

    if valid_to:
        try:
            # Handle both simple date format and ISO format with time for valid_to
            if "T" in valid_to:
                valid_to_date = datetime.strptime(valid_to.split("T")[0], "%Y-%m-%d")
            else:
                valid_to_date = datetime.strptime(valid_to, "%Y-%m-%d")

            if valid_from:
                if "T" in valid_from:
                    valid_from_date = datetime.strptime(valid_from.split("T")[0], "%Y-%m-%d")
                else:
                    valid_from_date = datetime.strptime(valid_from, "%Y-%m-%d")
                if valid_to_date.date() <= valid_from_date.date():
                    raise ValueError("validTo must be after validFrom")
            update_data["validTo"] = (
                valid_to if "T" in valid_to else f"{valid_to}T23:59:59.999Z"
            )
        except ValueError as e:
            if "strptime" in str(e):
                raise ValueError("validTo must be in YYYY-MM-DD format or ISO format with time")
            raise

    return update_data


def validate_card_data(credit_card_id: str, display_name: str, balance_cents: int, **kwargs) -> dict:
    """Validate card creation data."""

    if not balance_cents or balance_cents <= 0:
        raise ValueError("Balance must be greater than 0")

    data = {
        "creditCardId": credit_card_id,
        "displayName": display_name,
        "balanceCents": balance_cents
    }

    # Add any additional valid kwargs to the data
    for key, value in kwargs.items():
        if value is not None:
            data[key] = value

    return data
