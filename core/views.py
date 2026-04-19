from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Product, User, Sale, Category, SaleItem
from .forms import CategoryForm, ProductForm, RegisterForm
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth import login as auth_login
from .decorators import owner_required
from datetime import timedelta
from django.utils import timezone

def landing(request):
    if request.user.is_authenticated:
        return redirect('/dashboard')

    return render(request, 'landing.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    form = RegisterForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        user.role = 'customer'
        user.set_password(form.cleaned_data['password'])
        user.save()

        auth_login(request, user)

        return redirect('/dashboard/')

    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    total_products = Product.objects.count()
    total_users = User.objects.count()
    total_sales = Sale.objects.aggregate(total=Sum('total'))['total'] or 0
    user = request.user

    context = {
        'user': user,
        'total_products': total_products,
        'total_users': total_users,
        'total_sales': total_sales
    }

    return render(request, 'dashboard.html', context)

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'categories/list.html', {'categories': categories})

@owner_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'categories/form.html', {'form': form})

@owner_required
def category_edit(request, pk):
    category = Category.objects.get(id=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'categories/form.html', {'form': form})

@owner_required
def category_delete(request, pk):
    category = Category.objects.get(id=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'categories/delete.html', {'object': category})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})

@owner_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'products/form.html', {'form': form})

@owner_required
def product_edit(request, pk):
    product = Product.objects.get(id=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'products/form.html', {'form': form})

@owner_required
def product_delete(request, pk):
    product = Product.objects.get(id=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/delete.html', {'object': product})

@owner_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'users/list.html', {'users': users})

@owner_required
def user_delete(request, pk):
    user = User.objects.get(id=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'users/delete.html', {'object': user})

@owner_required
def sale_list(request):
    sales = Sale.objects.all()
    return render(request, 'sales/list.html', {'sales': sales})


@transaction.atomic
def create_sale(user, items):
    sale = Sale.objects.create(user=user, total=0)
    total = 0

    for item in items:
        product = Product.objects.get(id=item['product_id'])
        quantity = item['quantity']

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            price=product.price
        )

        product.quantity -= quantity
        product.save()

        total += product.price * quantity

    sale.total = total
    sale.save()

    return sale

def sale_create(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')

        items = []

        for i in range(len(product_ids)):
            items.append({
                'product_id': product_ids[i],
                'quantity': int(quantities[i])
            })

        create_sale(request.user, items)
        return redirect('/sales/')

    products = Product.objects.all()
    return render(request, 'sales/create.html', {'products': products})

@login_required
def revenue_report(request):
    time_limit = timezone.now() - timedelta(hours=24)
    revenue = Sale.objects.aggregate(total=Sum('total'))['total']
    last_24 = Sale.objects.filter(created_at__gte=time_limit).aggregate(total_24=Sum('total'))['total_24'] or 0
    return render(request, 'reports/revenue.html', {'revenue': revenue, 'last_24': last_24})

@login_required
def top_products(request):
    products = SaleItem.objects.values('product__name') \
        .annotate(total_sold=Sum('quantity')) \
        .order_by('-total_sold')[:10]

    return render(request, 'reports/top_products.html', {'products': products})

@login_required
def low_stock(request):
    products = Product.objects.filter(quantity__lt=5)
    return render(request, 'reports/low_stock.html', {'products': products})

def top_products(request):
    products = SaleItem.objects.values('product__name') \
        .annotate(total_sold=Sum('quantity')) \
        .order_by('-total_sold')[:5]

    return render(request, 'reports/top_products.html', {'products': products})