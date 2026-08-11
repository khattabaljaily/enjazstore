from decimal import Decimal

from .models import Coupon, CouponRedemption


class CouponError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def get_valid_coupon_for_cart(cart):
    """Returns the Coupon applied to this cart if it's still usable, else None."""
    if not cart.coupon_code:
        return None
    try:
        coupon = Coupon.objects.get(code=cart.coupon_code)
    except Coupon.DoesNotExist:
        return None
    if not coupon.is_valid_now():
        return None
    if coupon.minimum_order_amount and cart.total_price_sdg < coupon.minimum_order_amount:
        return None
    return coupon


def calculate_discount(cart):
    coupon = get_valid_coupon_for_cart(cart)
    if not coupon:
        return Decimal('0')
    return min(coupon.amount, cart.total_price_sdg)


def apply_coupon_to_cart(cart, code):
    """Validates a code against the cart's current subtotal and stores it. Raises CouponError if unusable."""
    try:
        coupon = Coupon.objects.get(code=code.upper().strip())
    except Coupon.DoesNotExist:
        raise CouponError('كود الخصم هذا غير موجود.')

    if not coupon.is_valid_now():
        raise CouponError('كود الخصم هذا لم يعد صالحاً.')

    if coupon.minimum_order_amount and cart.total_price_sdg < coupon.minimum_order_amount:
        raise CouponError(f'يتطلب هذا الكود حد أدنى للطلب قدره {coupon.minimum_order_amount:.2f} ج.س.')

    cart.coupon_code = coupon.code
    cart.save(update_fields=['coupon_code'])
    return coupon


def remove_coupon_from_cart(cart):
    cart.coupon_code = ''
    cart.save(update_fields=['coupon_code'])


def redeem_coupon_for_order(order, code):
    """Locks the coupon row, re-validates against the order's own totals/email, and
    records the redemption. Must be called inside a transaction.atomic() block by
    the caller so the lock and the order save commit together. Raises CouponError
    if the code can no longer be used (race lost, expired, per-customer cap hit)."""
    try:
        coupon = Coupon.objects.select_for_update().get(code=code.upper().strip())
    except Coupon.DoesNotExist:
        raise CouponError('كود الخصم هذا غير موجود.')

    if not coupon.is_valid_now():
        raise CouponError('كود الخصم هذا لم يعد صالحاً.')

    if coupon.minimum_order_amount and order.total < coupon.minimum_order_amount:
        raise CouponError(f'يتطلب هذا الكود حد أدنى للطلب قدره {coupon.minimum_order_amount:.2f} ج.س.')

    if not coupon.redemptions_left_for(order.email):
        raise CouponError('تم استخدام كود الخصم هذا بالفعل مع هذا البريد الإلكتروني.')

    discount = min(coupon.amount, order.total)
    CouponRedemption.objects.create(coupon=coupon, order=order, email=order.email, amount_applied=discount)

    order.coupon_code = coupon.code
    order.discount_total = discount
    return discount
