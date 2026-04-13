from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),

    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/new/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    path('sales/', views.sale_list , name='sale_list'),
    path('sales/new/', views.sale_create, name='sale_create'),

    path('reports/revenue/', views.revenue_report, name='revenue_report'),
    path('reports/top-products/', views.top_products, name='top_products'),
    path('reports/low-stock/', views.low_stock, name='low_stock'),
]