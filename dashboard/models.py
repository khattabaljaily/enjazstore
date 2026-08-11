from django.conf import settings
from django.db import models


class SiteSettings(models.Model):
    """Singleton row holding site-wide toggles controlled from the dashboard."""

    maintenance_mode = models.BooleanField(default=False)
    coming_soon_message = models.TextField(
        blank=True,
        default='نعمل على وضع اللمسات الأخيرة على شيء رائع. تابعونا قريبًا.',
    )
    ads_enabled = models.BooleanField(
        default=True,
        help_text='Show advertising banners on the homepage, cart, and checkout pages.',
    )

    # Bank transfer details shown to customers at checkout. Editable here so
    # the real account number can be filled in (and changed later) without
    # touching code.
    bank_name = models.CharField(max_length=100, default='بنك الخرطوم')
    bank_account_name = models.CharField(max_length=150, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    bank_transfer_note = models.CharField(
        max_length=255,
        blank=True,
        default='حوّل المبلغ عبر تطبيق بنكك (Bankak) إلى الحساب أعلاه، ثم ارفع صورة إيصال التحويل.',
    )
    delivery_estimate = models.CharField(max_length=100, default='2-4 أسابيع')

    # Product prices (Product.price / Variant.price_override) are stored in
    # USD so they don't need repricing every time the SDG rate moves. This is
    # the one number that converts them to SDG for display and at checkout —
    # update it whenever the rate changes. Defaults to 0 so a forgotten rate
    # shows as visibly broken (0 ج.س) rather than silently wrong.
    usd_to_sdg_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='كم جنيهًا سودانيًا يساوي الدولار الواحد الآن. حدّثه كل ما تغيّر السعر.',
    )

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return 'Site settings'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class VisitLog(models.Model):
    """One row per real page view, for the admin visitor-analytics report.

    Deliberately cookie-free: anonymous visitors are identified by a hash of
    IP + user agent salted with the current date, so nothing here is
    reversible to an IP and nothing can be correlated across days."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    location = models.CharField(max_length=100, blank=True)
    visitor_hash = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='visit_logs',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} — {self.location or "Unknown"}'
