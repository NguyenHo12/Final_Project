# Database Operations Module
# This module provides functions to interact with the database directly from Python code


from django.db import connection, models
from .models import Supply, AuditLog
from django.contrib.auth.models import User

def add_supply(name, price, quantity, location, reorder_point=5):
    """
    Add a new supply to the database
    
    Args:
        name (str): Name of the supply
        price (float): Price of the supply
        quantity (int): Quantity in stock
        location (str): Storage location
        reorder_point (int, optional): Minimum quantity before reorder. Defaults to 5.
    
    Returns:
        Supply: The created supply object or None if failed
    """
    try:
        supply = Supply.objects.create(
            name=name,
            price=price,
            quantity=quantity,
            location=location,
            reorder_point=reorder_point
        )
        return supply
    except Exception as e:
        print(f"Error adding supply: {e}")
        return None

def update_supply(name, **kwargs):
    """
    Update supply information in the database
    
    Args:
        name (str): Name of the supply to update
        **kwargs: Fields to update (price, quantity, location, reorder_point)
    
    Returns:
        Supply: The updated supply object or None if failed
    """
    try:
        supply = Supply.objects.get(name=name)
        for key, value in kwargs.items():
            setattr(supply, key, value)
        supply.save()
        return supply
    except Supply.DoesNotExist:
        print(f"Supply with name {name} does not exist")
        return None
    except Exception as e:
        print(f"Error updating supply: {e}")
        return None

def delete_supply(name):
    """
    Delete a supply from the database
    
    Args:
        name (str): Name of the supply to delete
    
    Returns:
        bool: True if successful, False if failed
    """
    try:
        supply = Supply.objects.get(name=name)
        supply.delete()
        return True
    except Supply.DoesNotExist:
        print(f"Supply with name {name} does not exist")
        return False
    except Exception as e:
        print(f"Error deleting supply: {e}")
        return False

def get_supply(name):
    """
    Retrieve a supply from the database
    
    Args:
        name (str): Name of the supply to retrieve
    
    Returns:
        Supply: The supply object or None if not found
    """
    try:
        return Supply.objects.get(name=name)
    except Supply.DoesNotExist:
        return None

def get_all_supplies():
    """
    Retrieve all supplies from the database
    
    Returns:
        QuerySet: All supply objects
    """
    return Supply.objects.all()

def get_low_stock_supplies():
    """
    Retrieve supplies with quantity below reorder point
    
    Returns:
        QuerySet: Supplies with low stock
    """
    return Supply.objects.filter(quantity__lte=models.F('reorder_point'))

def create_audit_log(user, action, supply, details):
    """
    Create an audit log entry
    
    Args:
        user (User): User who performed the action
        action (str): Type of action (CREATE, UPDATE, DELETE)
        supply (Supply): Supply that was affected
        details (str): Description of changes made
    
    Returns:
        AuditLog: The created audit log object or None if failed
    """
    try:
        return AuditLog.objects.create(
            user=user,
            action=action,
            supply=supply,
            details=details
        )
    except Exception as e:
        print(f"Error creating audit log: {e}")
        return None

def get_audit_logs():
    """
    Retrieve all audit logs, ordered by timestamp
    
    Returns:
        QuerySet: All audit log objects, newest first
    """
    return AuditLog.objects.all().order_by('-timestamp')

def execute_raw_sql(query, params=None):
    """
    Execute raw SQL query directly on the database
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
    
    Returns:
        list: Query results or None if failed
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return None 