"""Input checks, search-query parsing and the fixed value lists of the species database.

Only the Python standard library is used.
"""

from decimal import Decimal, InvalidOperation

CLASS_VALUES = ("Mammalia", "Aves", "Reptilia", "Amphibia", "Actinopterygii", "Insecta")
HABITAT_VALUES = ("Terrestrial", "Freshwater", "Marine", "Forest", "Grassland", "Desert", "Wetland")
DIET_VALUES = ("Herbivore", "Carnivore", "Omnivore", "Insectivore")
STATUS_LABELS = {
    "LC": "Least Concern",
    "NT": "Near Threatened",
    "VU": "Vulnerable",
    "EN": "Endangered",
    "CR": "Critically Endangered",
    "DD": "Data Deficient",
}
THREATENED_STATUSES = ("VU", "EN", "CR")

# Filter name (also the database column name) -> allowed values.
FILTER_VALUES = {
    "class_name": CLASS_VALUES,
    "habitat": HABITAT_VALUES,
    "diet": DIET_VALUES,
    "conservation_status": tuple(STATUS_LABELS.keys()),
}

MAX_SCIENTIFIC_NAME = 100
MAX_COMMON_NAME = 100
MAX_FAMILY = 100
MAX_DESCRIPTION = 1000
MIN_LIFESPAN = 1
MAX_LIFESPAN = 300
MAX_ADULT_MASS = Decimal("200000")

DUPLICATE_NAME_MESSAGE = "This scientific name is already registered."


def validate_species_fields(form):
    """Check the species form values and return (cleaned values, errors).

    Every field is checked, and each problem is reported under its field name.
    Optional fields that are left empty are stored as None (numbers) or "" (text).
    """
    errors = {}
    cleaned = {}

    scientific = _text(form, "scientific_name")
    if not 2 <= len(scientific) <= MAX_SCIENTIFIC_NAME:
        errors["scientific_name"] = "Scientific name is required (2 to 100 characters)."
    cleaned["scientific_name"] = scientific

    common = _text(form, "common_name")
    if not 1 <= len(common) <= MAX_COMMON_NAME:
        errors["common_name"] = "Common name is required (up to 100 characters)."
    cleaned["common_name"] = common

    cleaned["class_name"] = _choice(form, errors, "class_name", CLASS_VALUES, "Choose a class.")
    cleaned["habitat"] = _choice(form, errors, "habitat", HABITAT_VALUES, "Choose a habitat.")
    cleaned["diet"] = _choice(form, errors, "diet", DIET_VALUES, "Choose a diet.")
    cleaned["conservation_status"] = _choice(
        form, errors, "conservation_status", tuple(STATUS_LABELS.keys()), "Choose a conservation status."
    )

    family = _text(form, "family")
    if len(family) > MAX_FAMILY:
        errors["family"] = "Family must be 100 characters or fewer."
    cleaned["family"] = family

    lifespan_text = _text(form, "average_lifespan_years")
    cleaned["average_lifespan_years"] = None
    if lifespan_text:
        if lifespan_text.isdigit() and MIN_LIFESPAN <= int(lifespan_text) <= MAX_LIFESPAN:
            cleaned["average_lifespan_years"] = int(lifespan_text)
        else:
            errors["average_lifespan_years"] = "Average lifespan must be a whole number from 1 to 300."

    mass_text = _text(form, "average_adult_mass_kg")
    cleaned["average_adult_mass_kg"] = None
    if mass_text:
        mass = _parse_mass(mass_text)
        if mass is None:
            errors["average_adult_mass_kg"] = (
                "Average adult mass must be a number greater than 0 and at most 200000 (up to 2 decimals)."
            )
        else:
            cleaned["average_adult_mass_kg"] = mass

    description = _text(form, "description")
    if len(description) > MAX_DESCRIPTION:
        errors["description"] = "Description must be 1000 characters or fewer."
    cleaned["description"] = description

    return cleaned, errors


def parse_search_query(query):
    """Read the list-screen query values.

    Returns {"text": search text in lower case, "filters": {column: value}}.
    Empty values, "All" and values outside the fixed lists are ignored.
    """
    text = _text(query, "q").lower()
    filters = {}
    for name, allowed in FILTER_VALUES.items():
        value = _text(query, name)
        if value in allowed:
            filters[name] = value
    return {"text": text, "filters": filters}


def _text(form, key):
    value = form.get(key, "")
    if value is None:
        return ""
    return str(value).strip()


def _choice(form, errors, key, allowed, message):
    value = _text(form, key)
    if value in allowed:
        return value
    errors[key] = message
    return value


def _parse_mass(text):
    """Return the mass as a float rounded to 2 decimals, or None when invalid."""
    try:
        mass = Decimal(text)
    except InvalidOperation:
        return None
    if not mass.is_finite() or mass <= 0 or mass > MAX_ADULT_MASS:
        return None
    if mass != mass.quantize(Decimal("0.01")):
        return None
    return float(mass)
