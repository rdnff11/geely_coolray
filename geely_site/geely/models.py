from django.db import models
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Категория')
    slug = models.SlugField(max_length=100, unique=True)
    published = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['published']
        indexes = [models.Index(fields=['published'])]
        verbose_name = 'category'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('geely:cat_detail', args=[self.slug])


class Expense(models.Model):
    category = models.ForeignKey(Category, related_name='expenses', on_delete=models.CASCADE, verbose_name='КАТЕГОРИЯ',
                                 null=True, blank=True)
    date = models.DateField(default=timezone.now, verbose_name='ДАТА')
    mileage = models.CharField(default='НЕ УКАЗАН', verbose_name='ПРОБЕГ', null=True, blank=True)
    product = models.CharField(verbose_name='ПОКУПКА', null=True)
    service = models.CharField(verbose_name='РЕМОНТ / ТО', null=True)
    price = models.CharField(verbose_name='СТОИМОСТЬ', null=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Расходы'
