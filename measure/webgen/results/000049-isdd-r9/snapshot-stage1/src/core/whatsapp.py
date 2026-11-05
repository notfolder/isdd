"""WhatsApp click-to-chat links (wa.me). No external API is called."""

from urllib.parse import quote

WA_BASE = "https://wa.me/"


def split_phone_list(text):
    """Split a list of phone numbers typed one per line or separated by commas.

    Args:
        text: raw text from the form.
    Returns:
        list of non-empty, stripped strings in the order typed.
    """
    parts = []
    for line in text.replace(",", "\n").splitlines():
        item = line.strip()
        if item:
            parts.append(item)
    return parts


def build_whatsapp_link(digits, message):
    """Build a wa.me link that opens WhatsApp with the message filled in.

    Args:
        digits: phone number digits including the country code (no '+').
        message: the message text; it is URL-encoded.
    Returns:
        the link as a string.
    """
    return "%s%s?text=%s" % (WA_BASE, digits, quote(message, safe=""))
