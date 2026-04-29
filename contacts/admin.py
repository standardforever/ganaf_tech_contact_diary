from django.contrib import admin

# Register your models here.
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'email', 'company', 'created_at']
    search_fields = ['name', 'email', 'phone_number']
