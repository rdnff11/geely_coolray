from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Category, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['image']

    @admin.display(description="Изображение", ordering='name')
    def image(self, category: Category):
        if category.image:
            return mark_safe(f"<img src='{category.image.url}' width=50>")
        return "Без фото"

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'date', 'mileage', 'price']
    list_editable = ['mileage', 'price']
    list_filter = ['category', 'date']
