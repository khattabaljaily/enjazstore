from django.db import models

from orders.models import Order


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد الانتظار'
        PAID = 'paid', 'مدفوع'
        FAILED = 'failed', 'فشل'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    gateway = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_image = models.ImageField(upload_to='payment_receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Payment for Order #{self.order_id} ({self.get_status_display()})'
