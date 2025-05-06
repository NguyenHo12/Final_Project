from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from .models import Supply, AuditLog, Category, Tag, User
from .forms import SupplyForm, CategoryForm, TagForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import csv
from django.http import HttpResponse
from .forms import UploadFileForm
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password

# Helper function to check if user is editor or admin
def is_editor_or_admin(user):
    return user.is_staff or user.is_superuser

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

@login_required
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

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def export_supplies(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplies.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Price', 'Quantity', 'Location'])  # Header row
    for supply in Supply.objects.all():
        writer.writerow([supply.name, supply.price, supply.quantity, supply.location])
    return response

@login_required
@user_passes_test(is_editor_or_admin)
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
@user_passes_test(is_editor_or_admin)
def add_supply(request):
    if request.method == 'POST':
        form = SupplyForm(request.POST)
        if form.is_valid():
            supply = form.save()
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
@user_passes_test(is_editor_or_admin)
def delete_supply(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)
    supply_name = supply.name
    
    if request.method == 'POST':
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
    
    return render(request, 'inventory/supply_confirm_delete.html', {'supply': supply})

@login_required
@user_passes_test(is_editor_or_admin)
def edit_supply(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)
    if request.method == 'POST':
        form = SupplyForm(request.POST, instance=supply)
        if form.is_valid():
            old_data = f'{supply.name}, {supply.price}, {supply.quantity}, {supply.location}'
            supply = form.save()
            new_data = f'{supply.name}, {supply.price}, {supply.quantity}, {supply.location}'

            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                supply=supply,
                details=f'Updated supply: From {old_data} to {new_data}'
            )
            messages.success(request, 'Supply updated successfully!')
            return redirect('index')
    else:
        form = SupplyForm(instance=supply)
    return render(request, 'inventory/edit_supply.html', {'form': form, 'supply': supply})

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
@user_passes_test(is_editor_or_admin)
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

@login_required
@user_passes_test(is_editor_or_admin)
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

@login_required
@user_passes_test(is_editor_or_admin)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    # Check if category is used in any supplies
    linked_supplies = Supply.objects.filter(category=category)
    if linked_supplies.exists():
        supply_names = [supply.name for supply in linked_supplies[:5]]  # Get first 5 supplies
        if len(linked_supplies) > 5:
            supply_names.append(f"... and {len(linked_supplies) - 5} more")
        
        messages.error(request, 
            f'Cannot delete category "{category.name}" because it is used in the following supplies:\n'
            f'{", ".join(supply_names)}\n\n'
            f'Please remove or reassign these supplies to another category before deleting this category.'
        )
        return redirect('category_list')
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('category_list')
    
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})

@login_required
def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'inventory/tag_list.html', {'tags': tags})

@login_required
@user_passes_test(is_editor_or_admin)
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

@login_required
@user_passes_test(is_editor_or_admin)
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

@login_required
@user_passes_test(is_editor_or_admin)
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    
    # Check if tag is used in any supplies
    linked_supplies = Supply.objects.filter(tags=tag)
    if linked_supplies.exists():
        supply_names = [supply.name for supply in linked_supplies[:5]]  # Get first 5 supplies
        if len(linked_supplies) > 5:
            supply_names.append(f"... and {len(linked_supplies) - 5} more")
        
        messages.error(request, 
            f'Cannot delete tag "{tag.name}" because it is used in the following supplies:\n'
            f'{", ".join(supply_names)}\n\n'
            f'Please remove this tag from these supplies before deleting it.'
        )
        return redirect('tag_list')
    
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully.')
        return redirect('tag_list')
    
    return render(request, 'inventory/tag_confirm_delete.html', {'tag': tag})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'inventory/user_list.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('user_create')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('user_create')

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password1),
            is_active=is_active
        )

        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'editor':
            user.is_staff = True
            user.is_superuser = False
        else:  # viewer
            user.is_staff = False
            user.is_superuser = False

        user.save()
        messages.success(request, 'User created successfully.')
        return redirect('user_list')

    return render(request, 'inventory/user_form.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'

        if User.objects.filter(username=user.username).exclude(pk=pk).exists():
            messages.error(request, 'Username already exists.')
            return redirect('user_edit', pk=pk)

        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'editor':
            user.is_staff = True
            user.is_superuser = False
        else:  # viewer
            user.is_staff = False
            user.is_superuser = False

        user.is_active = is_active
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('user_list')

    return render(request, 'inventory/user_form.html', {'form': {'instance': user}})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, 'Cannot delete superuser.')
        return redirect('user_list')
    
    user.delete()
    messages.success(request, 'User deleted successfully.')
    return redirect('user_list')
