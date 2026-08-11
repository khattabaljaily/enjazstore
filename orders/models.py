import uuid

from django.conf import settings
from django.db import models

from products.models import Product, Variant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد الانتظار'
        PROCESSING = 'processing', 'قيد التجهيز'
        SHIPPED = 'shipped', 'تم الشحن'
        DELIVERED = 'delivered', 'تم التسليم'
        CANCELLED = 'cancelled', 'ملغى'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='orders', null=True, blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Unguessable public identifier for order confirmation/detail links, so
    # guest checkouts (no account) can view their own order without leaking
    # every other order via sequential-id enumeration.
    guest_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    address = models.TextField()
    city = models.CharField(max_length=100)

    coupon_code = models.CharField(max_length=32, blank=True)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # USD-to-SDG rate in effect when this order's item prices were converted
    # (see OrderItem.unit_price) — kept only for admin reference/reconciliation,
    # since unit_price/total are already the frozen SDG amounts either way.
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    tracking_carrier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk}'

    def recalculate_total(self):
        subtotal = sum((item.subtotal for item in self.items.all()), start=0)
        self.total = max(subtotal - self.discount_total, 0)
        self.save(update_fields=['total'])

    @property
    def is_cancellable(self):
        return self.status not in (self.Status.DELIVERED, self.Status.CANCELLED)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=200)
    variant_label = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    # Snapshotted at checkout time (like product_name/unit_price above) so a
    # later change to the product's condition or warranty never rewrites the
    # terms printed on a bill that already went out to a customer.
    condition = models.CharField(max_length=10, choices=Product.Condition.choices, default=Product.Condition.NEW)
    warranty_days = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class ReturnRequest(models.Model):
    class Reason(models.TextChoices):
        CHANGED_MIND = 'changed_mind', 'غيّرت رأيي'
        WRONG_ITEM = 'wrong_item', 'استلمت منتجًا خاطئًا'
        NO_LONGER_NEEDED = 'no_longer_needed', 'لم أعد بحاجته'
        DAMAGED = 'damaged', 'وصل المنتج تالفًا'
        DEFECTIVE = 'defective', 'المنتج به عيب'
        OTHER = 'other', 'سبب آخر'

    class Resolution(models.TextChoices):
        REFUND = 'refund', 'استرداد المبلغ'
        EXCHANGE = 'exchange', 'استبدال بمنتج آخر'
        REPLACEMENT = 'replacement', 'استبدال بنفس المنتج'

    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد المراجعة'
        APPROVED = 'approved', 'مقبول'
        REJECTED = 'rejected', 'مرفوض'
        COMPLETED = 'completed', 'مكتمل'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    reason = models.CharField(max_length=20, choices=Reason.choices)
    resolution_requested = models.CharField(max_length=20, choices=Resolution.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Return request #{self.pk} for order #{self.order_id}'

    @property
    def is_damage_claim(self):
        return self.reason in (self.Reason.DAMAGED, self.Reason.DEFECTIVE)
