from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Product
from .tasks import send_new_product_email


@receiver(post_save, sender=Product)
def product_create_signal(sender, instance, created, **kwargs):
    if created:
        print(f"Создан новый продукт: {instance.name}")

        created_by = "Система"
        if hasattr(instance, 'created_by') and instance.created_by:
            created_by = f"{instance.created_by.username} ({instance.created_by.email})"
        elif hasattr(instance, 'user') and instance.user:
            created_by = f"{instance.user.username} ({instance.user.email})"

        send_new_product_email.delay(
            product_id=instance.id,
            product_name=instance.name,
            product_price=getattr(instance, 'price', 'Не указана'),
            created_by=created_by
        )

    else:
        print(f"Обновлен продукт: {instance.name}")