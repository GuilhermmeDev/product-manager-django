from django.shortcuts import render, redirect
from django.http import JsonResponse
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
    user = request.user

    # Dashboard para Owner
    if user.role == 'owner':
        total_products = Product.objects.count()
        total_users = User.objects.count()
        total_sales = Sale.objects.aggregate(total=Sum('total'))['total'] or 0

        context = {
            'user': user,
            'total_products': total_products,
            'total_users': total_users,
            'total_sales': total_sales
        }
        return render(request, 'dashboard.html', context)

    # Dashboard para Customer
    else:
        total_products = Product.objects.count()
        customer_sales = Sale.objects.filter(user=user)
        total_spent = customer_sales.aggregate(total=Sum('total'))['total'] or 0
        total_purchases = customer_sales.count()
        recent_purchases = customer_sales.order_by('-created_at')[:5]

        context = {
            'user': user,
            'total_products': total_products,
            'total_spent': total_spent,
            'total_purchases': total_purchases,
            'recent_purchases': recent_purchases
        }
        return render(request, 'customer_dashboard.html', context)

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
    category = request.GET.get('category')
    if category is not None:
        products = Product.objects.filter(category__name=category)
    else:
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

@login_required
def sale_list(request):
    user = request.user

    # Owners veem todas as vendas
    if user.role == 'owner':
        sales = Sale.objects.all()
    # Customers veem apenas suas vendas
    else:
        sales = Sale.objects.filter(user=user)

    return render(request, 'sales/list.html', {'sales': sales})


@transaction.atomic
def create_sale(user, items):
    # First, validate stock availability
    for item in items:
        product = Product.objects.get(id=item['product_id'])
        if product.quantity < item['quantity']:
            raise ValueError(f'Estoque insuficiente para o produto "{product.name}". Disponível: {product.quantity}, solicitado: {item["quantity"]}')

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

        try:
            create_sale(request.user, items)
            return redirect('/sales/')
        except ValueError as e:
            # Add error message to context
            products = Product.objects.all()
            selected_product_id = request.GET.get('product')
            return render(request, 'sales/create.html', {
                'products': products,
                'selected_product_id': selected_product_id,
                'error_message': str(e)
            })

    products = Product.objects.all()

    # Pega o product_id da URL se foi passado
    selected_product_id = request.GET.get('product')

    return render(request, 'sales/create.html', {
        'products': products,
        'selected_product_id': selected_product_id
    })

@login_required
def revenue_report(request):
    # Get period from query parameters
    period = request.GET.get('period', '7d')  # default to 7 days
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    now = timezone.now()

    # Define time ranges based on period
    if period == '60min':
        time_limit = now - timedelta(minutes=60)
        prev_time_limit = time_limit - timedelta(minutes=60)
    elif period == '24h':
        time_limit = now - timedelta(hours=24)
        prev_time_limit = time_limit - timedelta(hours=24)
    elif period == '7d':
        time_limit = now - timedelta(days=7)
        prev_time_limit = time_limit - timedelta(days=7)
    elif period == '30d':
        time_limit = now - timedelta(days=30)
        prev_time_limit = time_limit - timedelta(days=30)
    elif period == 'custom' and start_date and end_date:
        try:
            start_dt = timezone.datetime.fromisoformat(start_date)
            end_dt = timezone.datetime.fromisoformat(end_date) + timedelta(days=1)  # include end date
            time_limit = timezone.make_aware(start_dt)
            prev_time_limit = time_limit - (end_dt - start_dt)  # same duration before
        except ValueError:
            # Fallback to 7 days if dates are invalid
            time_limit = now - timedelta(days=7)
            prev_time_limit = time_limit - timedelta(days=7)
    else:
        # Default to 7 days
        time_limit = now - timedelta(days=7)
        prev_time_limit = time_limit - timedelta(days=7)

    # Current period sales
    current_sales = Sale.objects.filter(created_at__gte=time_limit)
    prev_sales = Sale.objects.filter(created_at__gte=prev_time_limit, created_at__lt=time_limit)

    # Calculate metrics for current period
    revenue = current_sales.aggregate(total=Sum('total'))['total'] or 0
    sales_count = current_sales.count()
    avg_ticket = revenue / sales_count if sales_count > 0 else 0

    # Calculate metrics for previous period
    prev_revenue = prev_sales.aggregate(total=Sum('total'))['total'] or 0
    prev_sales_count = prev_sales.count()

    # Calculate growth rates
    revenue_change = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    sales_change = ((sales_count - prev_sales_count) / prev_sales_count * 100) if prev_sales_count > 0 else 0

    # Recent sales for the table (last 10 sales in the period)
    recent_sales = current_sales.select_related('user').order_by('-created_at')[:10]

    # Add items_count to each sale for the template
    for sale in recent_sales:
        sale.items_count = SaleItem.objects.filter(sale=sale).aggregate(count=Sum('quantity'))['count'] or 0

    # Chart data - sales by hour for the last 24 hours (for hourly chart)
    hourly_data = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)
        hour_sales = Sale.objects.filter(
            created_at__gte=hour_start,
            created_at__lt=hour_end
        ).aggregate(total=Sum('total'))['total'] or 0
        hourly_data.append({
            'hour': (now - timedelta(hours=i)).strftime('%H:00'),
            'revenue': float(hour_sales)
        })
    hourly_data.reverse()  # chronological order

    # Revenue trend data (daily for the period)
    trend_data = []
    days_in_period = (now - time_limit).days + 1
    for i in range(days_in_period):
        day_start = time_limit + timedelta(days=i)
        day_end = time_limit + timedelta(days=i+1)
        day_sales = Sale.objects.filter(
            created_at__gte=day_start,
            created_at__lt=day_end
        ).aggregate(total=Sum('total'))['total'] or 0
        trend_data.append({
            'date': day_start.strftime('%d/%m'),
            'revenue': float(day_sales)
        })

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'revenue': f"R$ {revenue:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'sales_count': sales_count,
            'avg_ticket': f"R$ {avg_ticket:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'revenue_change': f"{revenue_change:+.1f}%",
            'sales_change': f"{sales_change:+.1f}%",
            'trend_data': trend_data,
            'hourly_data': hourly_data,
            'recent_sales_count': recent_sales.count(),
        })

    context = {
        'period': period,
        'revenue': f"R$ {revenue:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'sales_count': sales_count,
        'avg_ticket': f"R$ {avg_ticket:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'revenue_change': f"{revenue_change:+.1f}%",
        'sales_change': f"{sales_change:+.1f}%",
        'recent_sales': recent_sales,
        'hourly_data': hourly_data,
        'trend_data': trend_data,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'reports/revenue.html', context)

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