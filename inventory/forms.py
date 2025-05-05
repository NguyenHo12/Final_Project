from django import forms
from .models import Supply, Category, Tag, PurchaseOrder, PurchaseOrderItem, Supplier
from django.utils import timezone

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ['name', 'price', 'quantity', 'reorder_point', 'location', 'category', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load all categories and tags
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a CSV file to upload')

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SupplierSelectForm(forms.Form):
    supplier = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter supplier name or select from dropdown',
            'list': 'supplier-list'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all active suppliers for the datalist
        self.suppliers = Supplier.objects.filter(is_active=True)

    def clean_supplier(self):
        supplier_name = self.cleaned_data['supplier']
        # Try to find existing supplier
        try:
            supplier = Supplier.objects.get(name__iexact=supplier_name)
            return supplier
        except Supplier.DoesNotExist:
            # Create new supplier if not found
            return Supplier.objects.create(
                name=supplier_name,
                is_active=True
            )

class PurchaseOrderForm(forms.ModelForm):
    supplier_form = SupplierSelectForm()

    class Meta:
        model = PurchaseOrder
        fields = ['expected_delivery_date', 'notes']
        widgets = {
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expected_delivery_date'].widget.attrs.update({'min': timezone.now().date().isoformat()})
        # Initialize supplier form with POST data if available
        if 'data' in kwargs:
            self.supplier_form = SupplierSelectForm(kwargs['data'])
        else:
            self.supplier_form = SupplierSelectForm()

    def is_valid(self):
        # Check if main form is valid
        is_valid = super().is_valid()
        # Check if supplier form is valid
        supplier_valid = self.supplier_form.is_valid()
        return is_valid and supplier_valid

    def clean(self):
        cleaned_data = super().clean()
        # Add supplier form data to cleaned data
        if self.supplier_form.is_valid():
            cleaned_data['supplier'] = self.supplier_form.cleaned_data['supplier']
        return cleaned_data

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['supply', 'quantity', 'notes']
        widgets = {
            'supply': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter any additional notes about this item'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load all supplies
        self.fields['supply'].queryset = Supply.objects.all()
        self.fields['supply'].label = "Product"
        self.fields['quantity'].label = "Quantity"
        self.fields['notes'].label = "Notes"

class PurchaseOrderStatusForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['status', 'payment_status', 'actual_delivery_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'actual_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }