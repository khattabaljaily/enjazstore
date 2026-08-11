from products.pricing import get_exchange_rate

from .utils import get_cart


def cart(request):
    if request.path.startswith('/api/'):
        return {}
    current_cart = get_cart(request)
    return {
        'cart_total_items': current_cart.total_items,
        'cart_total_price': current_cart.total_price_sdg,
        'exchange_rate': get_exchange_rate(),
    }
