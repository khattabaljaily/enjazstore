from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .emails import send_back_in_stock
from .models import ProductImage, Variant

_previous_stock_by_pk = {}


@receiver(post_delete, sender=ProductImage)
def delete_image_file(sender, instance, **kwargs):
    """Remove the image file from storage once its row is gone.

    Fires for direct ProductImage deletion and for the cascade delete
    that runs when a Product is deleted, so no orphaned files are left
    behind in media/products/ either way.
    """
    if instance.image:
        instance.image.delete(save=False)


@receiver(pre_save, sender=Variant)
def _capture_previous_stock(sender, instance, **kwargs):
    if instance.pk:
        _previous_stock_by_pk[instance.pk] = (
            Variant.objects.filter(pk=instance.pk).values_list('stock', flat=True).first()
        )


@receiver(post_save, sender=Variant)
def notify_stock_subscribers(sender, instance, created, **kwargs):
    """Email anyone waiting on a variant that just went from 0 to back in stock."""
    if created:
        return

    previous_stock = _previous_stock_by_pk.pop(instance.pk, None)
    if previous_stock != 0 or instance.stock <= 0:
        return

    subscriptions = list(instance.stock_subscriptions.all())
    for subscription in subscriptions:
        send_back_in_stock(subscription)
    instance.stock_subscriptions.all().delete()
