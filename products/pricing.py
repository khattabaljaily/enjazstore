from decimal import ROUND_HALF_UP, Decimal

from dashboard.models import SiteSettings


def get_exchange_rate():
    return SiteSettings.load().usd_to_sdg_rate


def to_sdg(usd_amount, rate=None):
    """Convert a USD amount to SDG using the current (or given) exchange rate."""
    if usd_amount is None:
        return None
    rate = get_exchange_rate() if rate is None else rate
    return (Decimal(usd_amount) * Decimal(rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
