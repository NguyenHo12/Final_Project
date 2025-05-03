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
from django.core.paginator import Paginator




def index(request):
    # Get filter parameters
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    search_query = request.GET.get('search', '')
    
    # Start with all supplies
    supplies = Supply.objects.all().select_related('category').prefetch_related('tags')
    
    # Apply filters if provided
    if category_id:
        supplies = supplies.filter(category_id=category_id)
    if tag_id:
        supplies = supplies.filter(tags__id=tag_id)
    if search_query:
        supplies = supplies.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    # Order by name
    supplies = supplies.order_by('name')
    
    # Paginate the supplies
    paginator = Paginator(supplies, 20)  # Show 20 supplies per page
    page_number = request.GET.get('page')
    supplies = paginator.get_page(page_number)
    
    # Get all categories and tags for the filter dropdowns
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'supplies': supplies,
        'categories': categories,
        'tags': tags,
        'selected_category': category_id,
        'selected_tag': tag_id,
        'search_query': search_query,
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

@login_required
def import_supplies(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                if file.name.endswith('.csv'):
                    # Handle CSV import
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) >= 2:
                            quantity = int(row[1])
                            supply.quantity += quantity
                            supply.save()
                            
                            # Log the import
                            AuditLog.objects.create(
                                supply=supply,
                                action='IMPORT',
                                quantity=quantity,
                                user=request.user
                            )
                            
                    messages.success(request, f'Successfully imported supplies for {supply.name}')
                    return redirect('index')
                else:
                    messages.error(request, 'Please upload a CSV file')
            except Exception as e:
                messages.error(request, f'Error importing supplies: {str(e)}')
    else:
        form = UploadFileForm()
    
    return render(request, 'inventory/import_supplies.html', {
        'form': form,
        'supply': supply
    })

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
def delete_supply(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)

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
def edit_supply(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)
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
    return render(request, 'inventory/edit_supply.html', {'form': form, 'supply': supply})

@login_required
@csrf_exempt 
def update_supply(request, supply_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        price = data.get('price')
        quantity = data.get('quantity')
        location = data.get('location')

        supply = get_object_or_404(Supply, id=supply_id)

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
