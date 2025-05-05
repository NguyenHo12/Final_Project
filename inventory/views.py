from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.db.models import F
from .models import Supply, AuditLog, Category, Tag, User, PurchaseOrder, Supplier, PurchaseOrderItem
from .forms import SupplyForm, CategoryForm, TagForm, PurchaseOrderForm, PurchaseOrderItemForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import csv
from django.http import HttpResponse, JsonResponse
from .forms import UploadFileForm
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal




def index(request):
    # Get filter parameters
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    location_query = request.GET.get('location', '')
    search_query = request.GET.get('search', '')
    
    # Start with all supplies
    supplies = Supply.objects.all().select_related('category').prefetch_related('tags')
    
    # Apply filters if provided
    if category_id:
        supplies = supplies.filter(category_id=category_id)
    if tag_id:
        supplies = supplies.filter(tags__id=tag_id)
    if location_query:
        supplies = supplies.filter(location__icontains=location_query)
    if search_query:
        supplies = supplies.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    # Order by name
    supplies = supplies.order_by('name')
    
    # Pagination
    paginator = Paginator(supplies, 20)  # Show 20 supplies per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories and tags for the filter dropdowns
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'supplies': page_obj,
        'categories': categories,
        'tags': tags,
        'selected_category': category_id,
        'selected_tag': tag_id,
        'location_query': location_query,
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

@login_required
def audit_log(request):
    # Get filter parameters
    action = request.GET.get('action')
    user_id = request.GET.get('user')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Start with all logs
    logs = AuditLog.objects.all().select_related('user', 'supply').order_by('-timestamp')
    
    # Apply filters if provided
    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 20)  # Show 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all users for the filter dropdown
    users = User.objects.all()
    
    context = {
        'logs': page_obj,
        'users': users,
        'selected_action': action,
        'selected_user': user_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'inventory/audit_log.html', context)

@login_required
def add_supply(request):
    if request.method == 'POST':
        form = SupplyForm(request.POST)
        if form.is_valid():
            supply = form.save()
            # Create an audit log entry for the new supply
            AuditLog.objects.create(
                supply=supply,
                supply_name=supply.name,
                action='CREATE',
                user=request.user,
                details=f"Created new supply: {supply.name}"
            )
            messages.success(request, f'New supply "{supply.name}" has been added.')
            return redirect('index')
    else:
        form = SupplyForm()
    return render(request, 'inventory/add_supply.html', {'form': form})

@login_required
def delete_supply(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)
    supply_name = supply.name  # Store the name before deletion
    
    # Create audit log before deleting
    AuditLog.objects.create(
        supply=supply,
        supply_name=supply_name,
        action='DELETE',
        user=request.user,
        details=f"Deleted supply: {supply_name}"
    )
    
    supply.delete()
    messages.success(request, f'Supply "{supply_name}" has been deleted.')
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
    supply = get_object_or_404(Supply, id=supply_id)
    if request.method == 'POST':
        form = SupplyForm(request.POST, instance=supply)
        if form.is_valid():
            form.save()
            # Create an audit log entry for the update
            AuditLog.objects.create(
                supply=supply,
                supply_name=supply.name,
                action='UPDATE',
                user=request.user,
                details=f"Updated supply: {supply.name}"
            )
            messages.success(request, f'Supply "{supply.name}" has been updated.')
            return redirect('index')
    else:
        form = SupplyForm(instance=supply)
    return render(request, 'inventory/edit_supply.html', {'form': form, 'supply': supply})

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

def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})

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

def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully.')
        return redirect('tag_list')
    return render(request, 'inventory/tag_confirm_delete.html', {'tag': tag})

@login_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.all().order_by('-order_date')
    return render(request, 'inventory/purchase_order_list.html', {'orders': orders})

@login_required
def purchase_order_detail(request, order_id):
    order = get_object_or_404(PurchaseOrder, id=order_id)
    items = order.items.all()
    return render(request, 'inventory/purchase_order_detail.html', {
        'order': order,
        'items': items
    })

@login_required
def create_purchase_order(request):
    if request.method == 'POST':
        supply_id = request.POST.get('supply')
        quantity = request.POST.get('quantity')
        notes = request.POST.get('notes', '')
        
        try:
            supply = Supply.objects.get(id=supply_id)
            
            # Create a supplier with the product name
            supplier, created = Supplier.objects.get_or_create(
                name=supply.name,
                defaults={
                    'contact_person': 'System',
                    'email': 'system@example.com',
                    'phone': 'N/A',
                    'address': 'N/A',
                    'notes': f'Auto-created supplier for product {supply.name}',
                    'is_active': True
                }
            )
            
            # Create purchase order
            order = PurchaseOrder.objects.create(
                supplier=supplier,
                order_date=timezone.now(),
                expected_delivery_date=timezone.now() + timedelta(days=7),
                status='PENDING',
                notes=notes,
                created_by=request.user
            )
            
            # Convert quantity to Decimal
            quantity_decimal = Decimal(str(quantity))
            unit_price = Decimal(str(supply.price))
            total_price = quantity_decimal * unit_price
            
            # Create order item
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                supply=supply,
                quantity=quantity_decimal,
                unit_price=unit_price,
                total_price=total_price,
                notes=notes
            )
            
            # Update order total
            order.total_amount = total_price
            order.save()
            
            messages.success(request, 'Purchase order created successfully.')
            return redirect('purchase_order_list')
            
        except Supply.DoesNotExist:
            messages.error(request, 'Selected supply does not exist.')
        except Exception as e:
            messages.error(request, f'Error creating purchase order: {str(e)}')
    
    # Get low stock items
    low_stock_items = Supply.objects.filter(
        quantity__lte=models.F('reorder_point')
    ).select_related('category')
    
    return render(request, 'inventory/purchase_order_form.html', {
        'low_stock_items': low_stock_items
    })

@login_required
def update_purchase_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(PurchaseOrder, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in ['RECEIVED', 'CANCELLED']:
            if new_status == 'RECEIVED':
                # Update inventory for each item
                for item in order.items.all():
                    supply = item.supply
                    supply.quantity += item.quantity
                    supply.save()
                    
                    # Create audit log
                    AuditLog.objects.create(
                        supply=supply,
                        action='RECEIVE',
                        user=request.user,
                        details=f'Received {item.quantity} units from purchase order {order.order_number}'
                    )
            
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {new_status.lower()}.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('purchase_order_detail', order_id=order_id)
