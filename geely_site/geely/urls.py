from django.urls import path
from . import views

app_name = 'geely'

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='cat_list'),
    path('<slug:slug>/', views.AddExpense.as_view(), name='cat_detail'),
]
