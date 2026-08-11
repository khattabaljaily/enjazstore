from django.shortcuts import render

from coupons.services import calculate_discount, get_valid_coupon_for_cart

from .utils import get_cart


def cart_detail(request):
    cart = get_cart(request)
    coupon = get_valid_coupon_for_cart(cart)
    discount = calculate_discount(cart)
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'coupon': coupon,
        'discount_amount': discount,
        'total_after_discount': cart.total_price_sdg - discount,
    })
