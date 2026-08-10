from rest_framework import serializers

from products.serializers import VariantSerializer

from coupons.services import calculate_discount, get_valid_coupon_for_cart

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    variant = VariantSerializer(read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'variant', 'product_name', 'quantity', 'subtotal')


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    coupon_code = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    total_after_discount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            'id', 'items', 'total_price', 'total_items',
            'coupon_code', 'discount_amount', 'total_after_discount',
        )

    def get_coupon_code(self, cart):
        coupon = get_valid_coupon_for_cart(cart)
        return coupon.code if coupon else None

    def get_discount_amount(self, cart):
        return calculate_discount(cart)

    def get_total_after_discount(self, cart):
        return cart.total_price - calculate_discount(cart)
