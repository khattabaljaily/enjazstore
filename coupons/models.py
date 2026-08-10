from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField(max_length=32, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='قيمة الخصم الثابتة، بالجنيه السوداني (ج.س).')
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    minimum_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Cart subtotal must reach this amount before the code can be applied. Leave blank for no minimum.',
    )
    max_redemptions = models.PositiveIntegerField(
        null=True, blank=True, help_text='Total times this code can be used across all customers. Leave blank for unlimited.',
    )
    max_redemptions_per_customer = models.PositiveIntegerField(
        null=True, blank=True, help_text='Leave blank for unlimited.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    @property
    def redemption_count(self):
        return self.redemptions.count()

    def is_valid_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_redemptions is not None and self.redemption_count >= self.max_redemptions:
            return False
        return True

    def redemptions_left_for(self, email):
        if self.max_redemptions_per_customer is None:
            return True
        used = self.redemptions.filter(email__iexact=email).count()
        return used < self.max_redemptions_per_customer


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='redemptions')
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='coupon_redemption')
    email = models.EmailField()
    amount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.coupon.code} on order #{self.order_id}'
