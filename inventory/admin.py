from django.contrib import admin
from .models import Supply, Category, Tag

class SupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'location', 'category')  
    search_fields = ('name', 'category__name')  
    list_filter = ('category', 'tags')
    ordering = ('name',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

admin.site.register(Supply, SupplyAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)


