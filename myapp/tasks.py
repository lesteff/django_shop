from celery import shared_task
import logging
import requests
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
import json

logger = logging.getLogger("api")


@shared_task
def add(x, y):
    return x + y


@shared_task
def scheduled_task():
    logger.info(">>> Периодическая задача выполнилась!")
    return True


@shared_task
def send_new_product_email(product_id, product_name, product_price, created_by):
    try:
        subject = f'🎉 Создан новый продукт: {product_name}'

        html_message = render_to_string('emails/new_product_email.html', {
            'product_name': product_name,
            'product_price': product_price,
            'created_by': created_by,
            'product_id': product_id,
        })


        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.ADMIN_EMAILS,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"✅ Email о создании продукта '{product_name}' отправлен на {settings.ADMIN_EMAILS}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка отправки email о создании продукта: {e}")
        return False


@shared_task
def send_daily_products_report():
    """
    Ежедневный отчет о созданных продуктах
    """
    try:
        from django.utils import timezone
        from .models import Product
        from datetime import timedelta

        yesterday = timezone.now() - timedelta(days=1)
        new_products = Product.objects.filter(created_at__gte=yesterday)

        subject = f'📊 Ежедневный отчет по продуктам ({yesterday.strftime("%d.%m.%Y")})'

        message = f"""
        Ежедневный отчет по новым продуктам:

        Всего новых продуктов за день: {new_products.count()}

        Список новых продуктов:
        {chr(10).join([f"- {product.name} (ID: {product.id})" for product in new_products])}

        ---
        Отчет сгенерирован автоматически.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.ADMIN_EMAILS,
            fail_silently=False,
        )

        logger.info(f"✅ Ежедневный отчет отправлен. Новых продуктов: {new_products.count()}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка отправки ежедневного отчета: {e}")
        return False


