from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product


@receiver(post_save, sender=Product)
def product_create_signal(sender, instance, created, **kwargs):
    if created:
        print(f"создан новый продукт: {instance.name}")
    else:
        print(f"Обновлен продукт: {instance.name}")
