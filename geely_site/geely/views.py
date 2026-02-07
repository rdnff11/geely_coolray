from datetime import datetime

from django.urls.base import reverse_lazy, reverse
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import ListView

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, FormView
from environs import Env

from .forms import AddExpenseForm, AddExpenseOtherForm, AddExpenseServiceForm

from .models import Category
import requests

env = Env()
env.read_env()

BOT_TOKEN = env('BOT_TOKEN')
CHAT_ID = env('CHAT_ID')


class CategoryListView(ListView):
    queryset = Category.objects.all()
    context_object_name = 'categories'
    template_name = 'geely/expense/cat_list.html'


class AddExpense(FormView):
    template_name = 'geely/expense/cat_detail.html'
    form_class = AddExpenseForm

    def dispatch(self, request, slug, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=slug)
        return super().dispatch(request, slug, *args, **kwargs)

    def get_form_class(self):
        if self.category.slug == 'prochee':
            return AddExpenseOtherForm
        if self.category.slug == 'remont':
            return AddExpenseServiceForm
        return AddExpenseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

    def form_valid(self, form):
        expense = form.save(commit=False)
        expense.category = self.category
        # expense.save()
        self.expense = expense
        self.request.session['preview_expense'] = {
            'date': str(expense.date),
            'category': expense.category.name,
            'mileage': expense.mileage,
            'product': expense.product,
            'service': expense.service,
            'price': expense.price,
        }
        return super().form_valid(form)

    def get_success_url(self):
        # self.send_message_to_telegram(self.expense)
        return reverse('geely:exam', kwargs={'slug': self.category.slug})


class ExamExpense(FormView):
    template_name = 'geely/expense/exam.html'
    form_class = AddExpenseForm

    def dispatch(self, request, slug, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=slug)
        return super().dispatch(request, slug, *args, **kwargs)

    def get_form_class(self):
        if self.category.slug == 'prochee':
            return AddExpenseOtherForm
        if self.category.slug == 'remont':
            return AddExpenseServiceForm
        return AddExpenseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        preview_expense = self.request.session.get('preview_expense')
        if preview_expense:
            context['preview_expense'] = preview_expense
        return context

    def form_valid(self, form, ):
        expense = form.save(commit=False)
        expense.category = self.category
        expense.save()
        if 'preview_expense' in self.request.session['preview_expense']:
            del self.request.session['preview_expense']
        self.expense = expense
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        preview_expense = self.request.session.get('preview_expense')
        if preview_expense:
            initial.update({
                'date': preview_expense.get('date', ''),
                'mileage': preview_expense.get('mileage', ''),
                'product': preview_expense.get('product', ''),
                'service': preview_expense.get('service', ''),
                'price': preview_expense.get('price', ''),
                'notes': preview_expense.get('notes', ''),
            })
        return initial

    def get_success_url(self):
        self.send_message_to_telegram(self.expense)
        return reverse('geely:success', kwargs={'slug': self.category.slug})

    def send_message_to_telegram(self, expense):
        if expense.mileage is None:
            expense.mileage = 'НЕ УКАЗАН'
        elif expense.mileage.isdigit():
            expense.mileage = str(int(expense.mileage) // 1000) + ' ' + str(expense.mileage[-3:]) + ' км'
        if len(expense.price) > 3:
            expense.price = str(int(expense.price) // 1000) + ' ' + expense.price[-3:]
        if self.category.slug == 'prochee':
            message = (
                "🚨 <b><u>НОВАЯ ПОКУПКА</u></b> 🚨\n\n"
                f"<b>📆   Дата:</b>   {expense.date.strftime('%d.%m.%Y г.')}\n"
                f"<b>🔢   Пробег:</b>   {expense.mileage.capitalize()}\n"
                f"<b>🛒   Покупка:</b>   {expense.product.capitalize()}\n"
                f"<b>💸   Стоимость:</b>   {expense.price} руб."
            )
        elif self.category.slug == 'remont':
            message = (
                "🚨 <b><u>НОВЫЙ РАСХОД ПО ОБСЛУЖИВАНИЮ</u></b> 🚨\n\n"
                f"<b>📆   Дата:</b>   {expense.date.strftime('%d.%m.%Y г.')}\n"
                f"<b>🔢   Пробег:</b>   {expense.mileage.capitalize()}\n"
                f"<b>⚙️   Ремонт / ТО:</b>   {expense.service}\n"
                f"<b>💸   Стоимость:</b>   {expense.price} руб."
            )
        else:
            message = (
                "🚨 <b><u>НОВЫЙ РАСХОД</u></b> 🚨\n\n"
                f"<b>📆   Дата:</b>   {expense.date.strftime('%d.%m.%Y г.')}\n"
                f"<b>🚙   Категория:</b>   {expense.category.name.capitalize()}\n"
                f"<b>🔢   Пробег:</b>   {expense.mileage.capitalize()}\n"
                f"<b>💸   Стоимость:</b>   {expense.price} руб."
            )

        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        params = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()


class SuccessExpense(ListView):
    queryset = Category.objects.all()
    context_object_name = 'categories'
    template_name = 'geely/expense/success.html'

    def dispatch(self, request, slug, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=slug)
        return super().dispatch(request, slug, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

    def get_success_url(self):
        return reverse('geely:cat_list')
