from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Category, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'date', 'mileage', 'product', 'service', 'price']
    list_editable = ['mileage', 'price']
    list_filter = ['category', 'date']
