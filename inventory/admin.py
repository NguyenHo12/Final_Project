

from django.contrib import admin
from .models import Supply

class SupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'location')  
    search_fields = ('name',)  
    ordering = ('name',)  


admin.site.register(Supply, SupplyAdmin)


