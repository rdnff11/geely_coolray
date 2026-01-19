from datetime import datetime

from django.utils import timezone

from django import forms
from .models import Category

from .models import Expense


class AddExpenseForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='ДАТА')
    # mileage = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'НЕ УКАЗАН'}))
    class Meta:
        model = Expense
        fields = ['date', 'mileage', 'price']
