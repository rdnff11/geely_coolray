from django.urls.base import reverse_lazy, reverse
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import ListView

from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import CreateView, FormView

from .forms import AddExpenseForm

from .models import Category


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['expense'] = getattr(self, 'expense', None)
        return context

    def form_valid(self, form):
        expense = form.save(commit=False)
        expense.category = self.category
        expense.save()
        self.expense = expense
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('geely:cat_list')
