from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('login/', views.custom_login, name='login'), 
    path('logout/', views.logout_view, name='logout'),
    path('low-stock/', views.low_stock_supplies, name='low_stock_supplies'), 
    path('audit-log/', views.audit_log, name='audit_log'),  
    path('add-supply/', views.add_supply, name='add_supply'),  
    path('delete-supply/<int:supply_id>/', views.delete_supply, name='delete_supply'),  
    path('edit-supply/<int:supply_id>/', views.edit_supply, name='edit_supply'),  
    path('export/', views.export_supplies, name='export_supplies'), 
    path('import/<int:supply_id>/', views.import_supplies, name='import_supplies'),  
    path('update_supply/<int:supply_id>/', views.update_supply, name='update_supply'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Tag URLs
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/update/', views.tag_update, name='tag_update'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),

    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.create_purchase_order, name='create_purchase_order'),
    path('purchase-orders/<int:order_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:order_id>/update-status/', views.update_purchase_order_status, name='update_purchase_order_status'),
]
