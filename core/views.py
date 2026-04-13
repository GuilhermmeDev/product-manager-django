from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Product, User, Sale, Category, SaleItem
from .forms import CategoryForm, ProductForm, RegisterForm
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth import login as auth_login

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


def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'categories/form.html', {'form': form})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})


def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'products/form.html', {'form': form})

def user_list(request):
    users = User.objects.all()
    return render(request, 'users/list.html', {'users': users})

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
    revenue = Sale.objects.aggregate(total=Sum('total'))['total']
    return render(request, 'reports/revenue.html', {'revenue': revenue})

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