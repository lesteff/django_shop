from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 4
    fields = ['image', 'is_main', 'order']

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'is_main':
            field.help_text = 'Отметьте чтобы сделать главным изображением'
        return field


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'in_stock', 'category', 'has_main_image')
    list_filter = ('in_stock', 'category')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]

    def has_main_image(self, obj):
        return obj.images.filter(is_main=True).exists()

    has_main_image.boolean = True
    has_main_image.short_description = 'Главное фото'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'order', 'image_preview')
    list_filter = ('product', 'is_main')
    list_editable = ('is_main', 'order')
    search_fields = ('product__name',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; {}" />',
                               obj.image.url,
                               'border: 2px solid green;' if obj.is_main else '')
        return "Нет изображения"

    image_preview.short_description = 'Превью'