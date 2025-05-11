from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('low-stock/', views.low_stock_supplies, name='low_stock'),
    path('audit-log/', views.audit_log, name='audit_log'),
    
    # Supply URLs
    path('supplies/add/', views.add_supply, name='add_supply'),
    path('supplies/<int:supply_id>/edit/', views.edit_supply, name='edit_supply'),
    path('supplies/<int:supply_id>/delete/', views.delete_supply, name='delete_supply'),
    path('supplies/<int:supply_id>/import/', views.import_supplies, name='import_supplies'),
    path('supplies/export/', views.export_supplies, name='export_supplies'),
    path('supplies/import/', views.import_all_supplies, name='import_all_supplies'),
    path('supplies/import/template/', views.download_import_template, name='download_import_template'),
    
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
    
    # User Management URLs
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]
