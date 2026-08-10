from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

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
