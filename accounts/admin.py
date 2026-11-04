from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'default_low_stock_threshold', 'created_at')
    search_fields = ('name', 'owner__username')
