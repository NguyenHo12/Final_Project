from django import forms
from .models import Supply, Category, Tag

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']

class SupplyForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Supply
        fields = ['name', 'price', 'quantity', 'location', 'reorder_point', 'category', 'tags']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'min': '0'}),
            'reorder_point': forms.NumberInput(attrs={'min': '0'}),
        }

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a CSV file to upload')