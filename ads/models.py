from django.db import models


class Banner(models.Model):
    class Placement(models.TextChoices):
        HOMEPAGE_1 = 'homepage_1', 'الصفحة الرئيسية - بانر 1'
        HOMEPAGE_2 = 'homepage_2', 'الصفحة الرئيسية - بانر 2'
        CART = 'cart', 'السلة'
        CHECKOUT = 'checkout', 'إتمام الطلب'

    name = models.CharField(max_length=150, help_text="Internal label - not shown to customers.")
    placement = models.CharField(max_length=20, choices=Placement.choices)
    image = models.ImageField(upload_to='banners/')
    target_url = models.URLField(help_text='External link the banner opens (in a new tab) when clicked.')
    alt_text = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers show first when more than one banner is active for the same placement.',
    )
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['placement', 'order', '-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_placement_display()})'

    @property
    def ctr(self):
        return (self.clicks / self.impressions * 100) if self.impressions else 0
