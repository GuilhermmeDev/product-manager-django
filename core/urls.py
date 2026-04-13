from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),

    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create, name='product_create'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/new/', views.category_create, name='category_create'),

    path('users/', views.user_list, name='user_list'),

    path('sales/', views.sale_list , name='sale_list'),
    path('sales/new/', views.sale_create, name='sale_create'),
    
    path('reports/revenue/', views.revenue_report, name='revenue_report'),
    path('reports/top-products/', views.top_products, name='top_products'),
    path('reports/low-stock/', views.low_stock, name='low_stock'),
    ]