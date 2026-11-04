from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'organization', 'quantity', 'selling_price', 'updated_at')
    list_filter = ('organization',)
    search_fields = ('name', 'sku')
