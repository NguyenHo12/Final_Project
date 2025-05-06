from django import forms
from .models import Supply, Category, Tag

class CategoryForm(forms.ModelForm):
    """
    Form for creating and editing categories.
    Fields: name (required), description (optional)
    """
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TagForm(forms.ModelForm):
    """
    Form for creating and editing tags.
    Fields: name (required)
    """
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SupplyForm(forms.ModelForm):
    """
    Form for creating and editing supplies.
    Fields: name, price, quantity, reorder_point, location, category, tags
    Includes validation for numeric fields and dynamic loading of categories/tags
    """
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
        # Load all categories and tags for dropdowns
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()

class UploadFileForm(forms.Form):
    """
    Form for uploading CSV files to import supplies.
    Fields: file (CSV file)
    """
    file = forms.FileField(label='Select a CSV file to upload')