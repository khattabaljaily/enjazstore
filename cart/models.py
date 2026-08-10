from django.conf import settings
from django.db import models

from products.models import Variant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart', null=True, blank=True,
    )
    session_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    coupon_code = models.CharField(max_length=32, blank=True)
    abandoned_email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart #{self.pk}'

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.select_related('variant__product')), start=0)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f'{self.quantity} x {self.variant}'

    @property
    def subtotal(self):
        return self.variant.price * self.quantity
