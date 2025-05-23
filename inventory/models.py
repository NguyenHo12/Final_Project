from django.db import models
from django.contrib.auth.models import User  # To link to the user making the change
from django.core.validators import MinValueValidator

class Category(models.Model):
    """
    Model representing a category for supplies.
    
    Attributes:
        name (str): Unique name of the category
        description (str): Optional description of the category
        created_at (datetime): Timestamp when the category was created
        updated_at (datetime): Timestamp when the category was last updated
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Tag(models.Model):
    """
    Model representing a tag that can be attached to supplies.
    
    Attributes:
        name (str): Unique name of the tag
        created_at (datetime): Timestamp when the tag was created
    """
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Supply(models.Model):
    """
    Model representing a supply item in the inventory.
    
    Attributes:
        name (str): Unique name of the supply
        price (decimal): Price of the supply (must be >= 0)
        quantity (int): Current quantity in stock (must be >= 0)
        location (str): Storage location of the supply
        reorder_point (int): Minimum quantity before reordering (must be >= 0)
        category (Category): Foreign key to Category model (optional)
        tags (Tag): Many-to-many relationship with Tag model
        created_at (datetime): Timestamp when the supply was created
        updated_at (datetime): Timestamp when the supply was last updated
    """
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    location = models.CharField(max_length=100)
    reorder_point = models.IntegerField(validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplies')
    tags = models.ManyToManyField(Tag, blank=True, related_name='supplies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Supplies"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        """
        Property that checks if the supply quantity is at or below reorder point.
        
        Returns:
            bool: True if quantity <= reorder_point, False otherwise
        """
        return self.quantity <= self.reorder_point

class AuditLog(models.Model):
    """
    Model for tracking all changes made to supplies in the inventory.
    
    Attributes:
        supply (Supply): Foreign key to Supply model (can be null if supply is deleted)
        supply_name (str): Name of the supply at the time of the action
        action (str): Type of action performed (CREATE, UPDATE, DELETE, IMPORT, EXPORT)
        timestamp (datetime): When the action was performed
        user (User): User who performed the action
        details (str): Additional details about the action
    """
    ACTION_CHOICES = (
        ('CREATE', 'CREATE'),
        ('UPDATE', 'UPDATE'),
        ('DELETE', 'DELETE'),
        ('IMPORT', 'IMPORT'),
        ('EXPORT', 'EXPORT'),
    )
    
    supply = models.ForeignKey(Supply, on_delete=models.SET_NULL, null=True)
    supply_name = models.CharField(max_length=100, default='Unknown')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.supply_name} - {self.timestamp}"

    def save(self, *args, **kwargs):
        """
        Override save method to ensure supply_name is set from supply if available.
        """
        if self.supply and not self.supply_name:
            self.supply_name = self.supply.name
        super().save(*args, **kwargs)
