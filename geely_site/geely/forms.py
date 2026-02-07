from datetime import datetime

from django.utils import timezone

from django import forms
from .models import Category

from .models import Expense


class AddExpenseForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='ДАТА')

    class Meta:
        model = Expense
        fields = ['date', 'mileage', 'price']


class AddExpenseOtherForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='ДАТА')

    class Meta:
        model = Expense
        fields = ['date', 'mileage', 'product', 'price']


class AddExpenseServiceForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='ДАТА')

    class Meta:
        model = Expense
        fields = ['date', 'mileage', 'service', 'price']
