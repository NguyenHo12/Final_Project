import os
import django
import random
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_project.settings')
django.setup()

from inventory.models import Category, Tag, Supply
from django.contrib.auth.models import User

def create_sample_data():
    # Create categories
    categories = [
        Category.objects.create(name='Food', description='Pet food and treats'),
        Category.objects.create(name='Toys', description='Pet toys and entertainment'),
        Category.objects.create(name='Health', description='Health and wellness products'),
        Category.objects.create(name='Grooming', description='Grooming and hygiene products'),
        Category.objects.create(name='Accessories', description='Pet accessories and supplies')
    ]

    # Create tags
    tags = [
        Tag.objects.create(name='Dog'),
        Tag.objects.create(name='Cat'),
        Tag.objects.create(name='Premium'),
        Tag.objects.create(name='Sale'),
        Tag.objects.create(name='New'),
        Tag.objects.create(name='Eco-friendly'),
        Tag.objects.create(name='Organic')
    ]

    # Create supplies
    supplies = [
        {
            'name': 'Premium Dog Food',
            'price': Decimal('49.99'),
            'quantity': 50,
            'location': 'A1',
            'reorder_point': 10,
            'category': categories[0],
            'tags': [tags[0], tags[2], tags[4]]
        },
        {
            'name': 'Cat Litter',
            'price': Decimal('24.99'),
            'quantity': 30,
            'location': 'B2',
            'reorder_point': 5,
            'category': categories[3],
            'tags': [tags[1], tags[5]]
        },
        {
            'name': 'Dog Chew Toy',
            'price': Decimal('12.99'),
            'quantity': 25,
            'location': 'C3',
            'reorder_point': 8,
            'category': categories[1],
            'tags': [tags[0], tags[3]]
        },
        {
            'name': 'Cat Scratching Post',
            'price': Decimal('39.99'),
            'quantity': 15,
            'location': 'D4',
            'reorder_point': 3,
            'category': categories[1],
            'tags': [tags[1], tags[4]]
        },
        {
            'name': 'Organic Dog Treats',
            'price': Decimal('19.99'),
            'quantity': 40,
            'location': 'A2',
            'reorder_point': 10,
            'category': categories[0],
            'tags': [tags[0], tags[2], tags[5], tags[6]]
        },
        {
            'name': 'Cat Food Bowl Set',
            'price': Decimal('15.99'),
            'quantity': 20,
            'location': 'B3',
            'reorder_point': 5,
            'category': categories[4],
            'tags': [tags[1], tags[4]]
        },
        {
            'name': 'Dog Shampoo',
            'price': Decimal('14.99'),
            'quantity': 35,
            'location': 'C4',
            'reorder_point': 8,
            'category': categories[3],
            'tags': [tags[0], tags[5]]
        },
        {
            'name': 'Cat Carrier',
            'price': Decimal('45.99'),
            'quantity': 10,
            'location': 'D5',
            'reorder_point': 2,
            'category': categories[4],
            'tags': [tags[1], tags[2]]
        },
        {
            'name': 'Dog Training Pads',
            'price': Decimal('29.99'),
            'quantity': 30,
            'location': 'A3',
            'reorder_point': 10,
            'category': categories[4],
            'tags': [tags[0], tags[3]]
        },
        {
            'name': 'Cat Dental Treats',
            'price': Decimal('12.99'),
            'quantity': 45,
            'location': 'B4',
            'reorder_point': 15,
            'category': categories[2],
            'tags': [tags[1], tags[6]]
        },
        {
            'name': 'Dog Bed',
            'price': Decimal('59.99'),
            'quantity': 12,
            'location': 'C5',
            'reorder_point': 3,
            'category': categories[4],
            'tags': [tags[0], tags[2]]
        },
        {
            'name': 'Cat Tree',
            'price': Decimal('89.99'),
            'quantity': 8,
            'location': 'D6',
            'reorder_point': 2,
            'category': categories[1],
            'tags': [tags[1], tags[4]]
        },
        {
            'name': 'Dog Collar',
            'price': Decimal('19.99'),
            'quantity': 25,
            'location': 'A4',
            'reorder_point': 5,
            'category': categories[4],
            'tags': [tags[0], tags[3]]
        },
        {
            'name': 'Cat Food',
            'price': Decimal('34.99'),
            'quantity': 40,
            'location': 'B5',
            'reorder_point': 10,
            'category': categories[0],
            'tags': [tags[1], tags[2]]
        },
        {
            'name': 'Dog Leash',
            'price': Decimal('24.99'),
            'quantity': 30,
            'location': 'C6',
            'reorder_point': 8,
            'category': categories[4],
            'tags': [tags[0], tags[5]]
        },
        {
            'name': 'Cat Toy Set',
            'price': Decimal('18.99'),
            'quantity': 35,
            'location': 'D7',
            'reorder_point': 10,
            'category': categories[1],
            'tags': [tags[1], tags[3]]
        },
        {
            'name': 'Dog Vitamins',
            'price': Decimal('29.99'),
            'quantity': 20,
            'location': 'A5',
            'reorder_point': 5,
            'category': categories[2],
            'tags': [tags[0], tags[2]]
        },
        {
            'name': 'Cat Grooming Kit',
            'price': Decimal('22.99'),
            'quantity': 15,
            'location': 'B6',
            'reorder_point': 3,
            'category': categories[3],
            'tags': [tags[1], tags[4]]
        },
        {
            'name': 'Dog Training Clicker',
            'price': Decimal('9.99'),
            'quantity': 50,
            'location': 'C7',
            'reorder_point': 15,
            'category': categories[4],
            'tags': [tags[0], tags[3]]
        },
        {
            'name': 'Cat Window Perch',
            'price': Decimal('34.99'),
            'quantity': 10,
            'location': 'D8',
            'reorder_point': 2,
            'category': categories[4],
            'tags': [tags[1], tags[2]]
        }
    ]

    # Create supplies
    for supply_data in supplies:
        supply = Supply.objects.create(
            name=supply_data['name'],
            price=supply_data['price'],
            quantity=supply_data['quantity'],
            location=supply_data['location'],
            reorder_point=supply_data['reorder_point'],
            category=supply_data['category']
        )
        supply.tags.set(supply_data['tags'])

    print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data() 