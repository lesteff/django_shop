from django.db import models
from django.contrib.auth.models import User
from django.db.models import ForeignKey


# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название продукта")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    in_stock = models.BooleanField(default=True, verbose_name="В наличии")
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория"
    )

    def get_images_with_fallback(self):
        """Возвращает 4 изображения с заполнением no-image.png"""
        images = []

        # Получаем главное изображение
        main_image = self.images.filter(is_main=True).first()
        # Получаем остальные изображения
        other_images = self.images.filter(is_main=False).order_by('order', 'id')

        real_images = []
        if main_image:
            real_images.append(main_image)
        real_images.extend(other_images)
        real_images = real_images[:4]  # Берем максимум 4

        for i in range(4):
            if i < len(real_images):
                images.append({
                    'image': real_images[i].image,
                    'is_real': True,
                    'is_main': real_images[i].is_main
                })
            else:
                images.append({
                    'image': None,
                    'is_real': False,
                    'is_main': False
                })

        return images

    def get_main_image(self):
        """Возвращает главное изображение или первое доступное"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image.image
        first_image = self.images.first()
        if first_image:
            return first_image.image
        return None


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Продукт"
    )
    image = models.ImageField(upload_to='product_images/', verbose_name="Изображение")
    is_main = models.BooleanField(default=False, verbose_name="Главное изображение")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def save(self, *args, **kwargs):
        # Если это изображение помечено как главное, снимаем флаг с других
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ограничение на 4 изображения на товар
        if self.product.images.count() >= 4 and not self.pk:
            raise ValidationError("Нельзя добавить более 4 изображений для одного товара")

    class Meta:
        ordering = ['order', 'id']


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона")
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента", blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Заказ #{self.id} - {self.phone_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


