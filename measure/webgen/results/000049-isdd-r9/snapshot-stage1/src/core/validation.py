"""Input validation for the barber shop site (rules D7 to D9 in docs/requirements.md)."""

import re
from decimal import Decimal, InvalidOperation

from core.whatsapp import split_phone_list

NAME_MAX = 60
SPECIALTY_MAX = 100
SERVICE_NAME_MAX = 80
DESCRIPTION_MAX = 300
MESSAGE_MAX = 500
PRICE_MAX_CENTS = 1000000
DURATION_MIN = 5
DURATION_MAX = 480
MAX_NUMBERS = 20

PHONE_ALLOWED = re.compile(r"^\+?[0-9 \-()]+$")


class ValidationError(Exception):
    """Raised when one or more form fields are invalid.

    Attributes:
        errors: list of English error messages, one per problem.
    """

    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = list(errors)


def normalize_phone(text):
    """Return the digits of a phone number, or None when the format is invalid.

    Args:
        text: the phone number as typed. An optional leading '+' is allowed,
            followed by digits, spaces, hyphens or parentheses.
    Returns:
        A string of 8 to 15 digits, or None.
    """
    text = text.strip()
    if not PHONE_ALLOWED.match(text):
        return None
    digits = re.sub(r"\D", "", text)
    if not 8 <= len(digits) <= 15:
        return None
    return digits


def _text(form, key):
    """Return a form value as a stripped string."""
    return (form.get(key) or "").strip()


def validate_barber_form(form):
    """Check the Add barber form.

    Args:
        form: mapping with keys name, specialty, phone.
    Returns:
        dict with keys name, specialty, phone (phone as typed, stripped).
    Raises:
        ValidationError: when any field breaks rules D7.
    """
    errors = []
    name = _text(form, "name")
    specialty = _text(form, "specialty")
    phone = _text(form, "phone")
    if not name:
        errors.append("Name is required.")
    elif len(name) > NAME_MAX:
        errors.append("Name must be %d characters or fewer." % NAME_MAX)
    if len(specialty) > SPECIALTY_MAX:
        errors.append("Specialty must be %d characters or fewer." % SPECIALTY_MAX)
    if phone and normalize_phone(phone) is None:
        errors.append('Phone "%s" is not valid. Use 8 to 15 digits, with country code.' % phone)
    if errors:
        raise ValidationError(errors)
    return {"name": name, "specialty": specialty, "phone": phone}


def validate_service_form(form):
    """Check the Add service form.

    Args:
        form: mapping with keys name, price, duration_min, description.
    Returns:
        dict with keys name, price_cents (int), duration_min (int), description.
    Raises:
        ValidationError: when any field breaks rules D8.
    """
    errors = []
    name = _text(form, "name")
    price_text = _text(form, "price")
    duration_text = _text(form, "duration_min")
    description = _text(form, "description")
    if not name:
        errors.append("Name is required.")
    elif len(name) > SERVICE_NAME_MAX:
        errors.append("Name must be %d characters or fewer." % SERVICE_NAME_MAX)

    price_cents = None
    if not price_text:
        errors.append("Price is required.")
    else:
        try:
            price = Decimal(price_text)
            if not price.is_finite() or price.as_tuple().exponent < -2:
                raise InvalidOperation
            price_cents = int(price * 100)
            if not 0 <= price_cents <= PRICE_MAX_CENTS:
                errors.append("Price must be between 0 and 10000.")
                price_cents = None
        except (InvalidOperation, ValueError):
            errors.append("Price must be a number with at most 2 decimal places.")

    duration = None
    if not duration_text:
        errors.append("Duration is required.")
    elif not re.match(r"^[0-9]+$", duration_text):
        errors.append("Duration must be a whole number of minutes.")
    else:
        duration = int(duration_text)
        if not DURATION_MIN <= duration <= DURATION_MAX:
            errors.append("Duration must be between 5 and 480 minutes.")
            duration = None

    if len(description) > DESCRIPTION_MAX:
        errors.append("Description must be %d characters or fewer." % DESCRIPTION_MAX)
    if errors:
        raise ValidationError(errors)
    return {
        "name": name,
        "price_cents": price_cents,
        "duration_min": duration,
        "description": description,
    }


def validate_notify_form(form):
    """Check the Notify form.

    Args:
        form: mapping with keys phones (text, one number per line or comma separated)
            and message.
    Returns:
        dict with keys numbers (list of digit strings) and message (stripped).
    Raises:
        ValidationError: when the list is empty or too long, a number is invalid,
            or the message is empty or too long (rules D9).
    """
    errors = []
    raw_numbers = split_phone_list(form.get("phones") or "")
    message = _text(form, "message")
    numbers = []
    if not raw_numbers:
        errors.append("Enter at least one phone number.")
    elif len(raw_numbers) > MAX_NUMBERS:
        errors.append("Enter at most %d phone numbers." % MAX_NUMBERS)
    else:
        for raw in raw_numbers:
            digits = normalize_phone(raw)
            if digits is None:
                errors.append('Phone "%s" is not valid. Use 8 to 15 digits, with country code.' % raw)
            else:
                numbers.append(digits)
    if not message:
        errors.append("Message is required.")
    elif len(message) > MESSAGE_MAX:
        errors.append("Message must be %d characters or fewer." % MESSAGE_MAX)
    if errors:
        raise ValidationError(errors)
    return {"numbers": numbers, "message": message}
