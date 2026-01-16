from django import forms
from .models import Category

from .models import Expense


class AddExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'mileage', 'price']
