from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

from products.pricing import to_sdg

register = template.Library()


@register.filter
def money(value):
    """Format a price as a whole-number, thousands-separated string (e.g. 1,000)."""
    if value in (None, ''):
        return ''
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value
    amount = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return f'{amount:,}'


@register.filter
def sdg(usd_value, rate):
    """Convert a USD amount to SDG at the given rate, then format like `money`."""
    if usd_value in (None, '') or rate in (None, ''):
        return ''
    try:
        amount = to_sdg(usd_value, rate)
    except (InvalidOperation, ValueError, TypeError):
        return ''
    return money(amount)


@register.filter
def sdg_raw(usd_value, rate):
    """Like `sdg`, but returns a plain unformatted number (no thousands
    separator) — for machine-readable contexts like JSON-LD, not display."""
    if usd_value in (None, '') or rate in (None, ''):
        return ''
    try:
        return to_sdg(usd_value, rate)
    except (InvalidOperation, ValueError, TypeError):
        return ''
