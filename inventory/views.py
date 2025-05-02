from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from .models import Supply, AuditLog, Category, Tag  # Make sure to import AuditLog, Category, and Tag
from .forms import SupplyForm, CategoryForm, TagForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import csv
from django.http import HttpResponse, JsonResponse
from .forms import UploadFileForm
from django.views.decorators.csrf import csrf_exempt
import json




def index(request):
    location_query = request.GET.get('location', '')
    name_query = request.GET.get('name', '')
    category_query = request.GET.get('category', '')
    tag_query = request.GET.get('tag', '')
    low_stock = request.GET.get('low_stock', False)

    supplies = Supply.objects.all().select_related('category').prefetch_related('tags')

    if low_stock:
        supplies = supplies.filter(quantity__lte=models.F('reorder_point'))

    if location_query:
        supplies = supplies.filter(location__icontains=location_query)
    if name_query:
        supplies = supplies.filter(name__icontains=name_query)
    if category_query:
        supplies = supplies.filter(category_id=category_query)
    if tag_query:
        supplies = supplies.filter(tags__id=tag_query)

    if request.method == 'POST':
        supply_name = request.POST.get('supply_name')
        quantity_returned = int(request.POST.get('quantity', 0))
        supply = get_object_or_404(Supply, name=supply_name)

        if quantity_returned > 0:
            supply.quantity += quantity_returned
            supply.save()
            messages.success(request, f'Supply {supply_name} returned successfully! New quantity: {supply.quantity}')
        else:
            messages.error(request, 'Invalid quantity returned. Please enter a positive number.')

    low_stock_items = Supply.objects.filter(quantity__lte=models.F('reorder_point'))
    low_stock_items_exist = low_stock_items.exists()

    # Get all categories and tags for the filter dropdowns
    categories = Category.objects.all()
    tags = Tag.objects.all()

    context = { 
        'supplies': supplies,
        'low_stock_items': low_stock_items,
        'location_query': location_query,
        'name_query': name_query,
        'category_query': category_query,
        'tag_query': tag_query,
        'low_stock_items_exist': low_stock_items_exist,
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'inventory/index.html', context)

def low_stock_supplies(request):
    low_stock_items = Supply.objects.filter(quantity__lte=models.F('reorder_point'))
    return render(request, 'inventory/low_stock.html', {'low_stock_items': low_stock_items})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'inventory/login.html')

def export_supplies(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplies.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Price', 'Quantity', 'Location'])  # Header row
    for supply in Supply.objects.all():
        writer.writerow([supply.name, supply.price, supply.quantity, supply.location])
    return response

def import_supplies(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            reader = csv.reader(file.read().decode('utf-8').splitlines())
            next(reader)  
            for row in reader:
                Supply.objects.create(name=row[0], price=row[1], quantity=row[2], location=row[3])
            return redirect('index') 
    else:
        form = UploadFileForm()
    return render(request, 'inventory/import_supplies.html', {'form': form})

def audit_log(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'inventory/audit_log.html', {'logs': logs})

@login_required
def add_supply(request):
    if request.method == 'POST':
        form = SupplyForm(request.POST)
        if form.is_valid():
            supply = form.save()

            # Create an audit log entry
            AuditLog.objects.create(
                user=request.user,  # User who made the change
                action='CREATE',  # Action type
                supply=supply,  # The supply that was created
                details=f'Created supply: {supply.name}, {supply.price}, {supply.quantity}, {supply.location}'  # Description of the changes
            )
            messages.success(request, 'Supply added successfully!')
            return redirect('index')
    else:
        form = SupplyForm()
    return render(request, 'inventory/add_supply.html', {'form': form})

@login_required
def delete_supply(request, supply_name):
    supply = get_object_or_404(Supply, name=supply_name)

    if request.method == 'POST':
        # Create audit log before deleting
        AuditLog.objects.create(
            user=request.user,
            action='DELETE',
            supply=supply,
            details=f'Deleted supply: {supply.name}, {supply.price}, {supply.quantity}, {supply.location}'
        )
        supply.delete()  # Actually delete the supply
        messages.success(request, 'Supply deleted successfully!')
        return redirect('index')
    
    messages.error(request, 'Invalid request method for deletion.')
    return redirect('index')

@login_required
def edit_supply(request, supply_name):
    supply = get_object_or_404(Supply, name=supply_name)
    if request.method == 'POST':
        form = SupplyForm(request.POST, instance=supply)
        if form.is_valid():
    
            old_data = f'{supply.name}, {supply.price}, {supply.quantity}, {supply.location}'
            supply = form.save()
            new_data = f'{supply.name}, {supply.price}, {supply.quantity}, {supply.location}'

            # Create an audit log entry for the update
            AuditLog.objects.create(
                user=request.user,  # User who made the change
                action='UPDATE',  # Action type
                supply=supply,  # The supply that was updated
                details=f'Updated supply: From {old_data} to {new_data}'  # Description of what was changed
            )
            messages.success(request, 'Supply updated successfully!')
            return redirect('index')
    else:
        form = SupplyForm(instance=supply)
    return render(request, 'inventory/edit_supply.html', {'form': form})

@login_required
@csrf_exempt 
def update_supply(request, supply_name):
    if request.method == 'POST':
        data = json.loads(request.body)
        price = data.get('price')
        quantity = data.get('quantity')
        location = data.get('location')

        
        supply = get_object_or_404(Supply, name=supply_name)

        changes = []
        if price is not None and price != str(supply.price):
            changes.append(f"Price changed from ${supply.price} to ${price}")
            supply.price = price
        if quantity is not None and quantity != str(supply.quantity):
            changes.append(f"Quantity changed from {supply.quantity} to {quantity}")
            supply.quantity = quantity 
        if location is not None and location != supply.location:
            changes.append(f"Location changed from '{supply.location}' to '{location}'")
            supply.location = location

        
        supply.save()

     
        if changes:
            AuditLog.objects.create(
                action='Update',
                user=request.user,  
                supply=supply,
                details='; '.join(changes)
            )

        return JsonResponse({'status': 'success', 'message': 'Supply updated successfully.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

def logout_view(request):
    logout(request)
    return redirect('index')

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Create Category'})

def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Update Category'})

def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'inventory/tag_list.html', {'tags': tags})

def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully.')
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'inventory/tag_form.html', {'form': form, 'title': 'Create Tag'})

def tag_update(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully.')
            return redirect('tag_list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'inventory/tag_form.html', {'form': form, 'title': 'Update Tag'})
