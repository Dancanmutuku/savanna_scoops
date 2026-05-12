from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Flavor, SiteSettings
from inventory.models import InventoryItem, AuditLog
from orders.models import Order, OrderItem, OrderStatusHistory
from decimal import Decimal
import random


FLAVORS = [
    {
        'name': 'Kenyan Dark Chocolate',
        'description': 'Rich single-origin dark chocolate from Mount Kenya estates, slow-churned with a hint of espresso and sea salt. Velvety smooth finish.',
        'price': Decimal('450.00'),
        'color_hex': '#3D1A0A',
        'category': 'classic',
        'stock': 180,
        'is_featured': True,
        'rating': Decimal('4.9'),
        'total_sales': 342,
        'image_url': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Mango Maziwa',
        'description': 'Fresh Malindi mangoes blended with creamy whole milk and a dash of cardamom. Tastes like a Kenyan summer afternoon.',
        'price': Decimal('380.00'),
        'color_hex': '#FFA827',
        'category': 'fruity',
        'stock': 150,
        'is_featured': True,
        'rating': Decimal('4.8'),
        'total_sales': 289,
        'is_dairy_free': False,
        'image_url': 'https://images.unsplash.com/photo-1501443762994-82bd5dace89a?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Passion & Hibiscus Sorbet',
        'description': 'Zero-dairy sorbet of wild passion fruit and dried hibiscus flowers. Tangy, floral, and utterly refreshing.',
        'price': Decimal('350.00'),
        'color_hex': '#E91E8C',
        'category': 'sorbet',
        'stock': 120,
        'is_dairy_free': True,
        'is_featured': True,
        'rating': Decimal('4.7'),
        'total_sales': 215,
        'image_url': 'https://images.unsplash.com/photo-1488900128323-21503983a07e?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Vanilla Bean Royale',
        'description': 'Tahitian vanilla beans steeped in fresh cream overnight. Classic, pure, and utterly indulgent.',
        'price': Decimal('420.00'),
        'color_hex': '#FFF8DC',
        'category': 'classic',
        'stock': 200,
        'is_featured': False,
        'rating': Decimal('4.6'),
        'total_sales': 178,
        'image_url': 'https://images.unsplash.com/photo-1570197788417-0e82375c9371?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Salted Caramel Savanna',
        'description': 'House-made caramel with Maldon sea salt, swirled through Madagascar cream. Our best-seller since 2015.',
        'price': Decimal('480.00'),
        'color_hex': '#C68642',
        'category': 'classic',
        'stock': 160,
        'is_featured': True,
        'rating': Decimal('4.9'),
        'total_sales': 410,
        'image_url': 'https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Baobab & Coconut',
        'description': 'Baobab superfruit powder meets creamy coconut milk for a dairy-free tropical dream with a subtle citrus note.',
        'price': Decimal('400.00'),
        'color_hex': '#D4C5A9',
        'category': 'sorbet',
        'stock': 90,
        'is_dairy_free': True,
        'is_featured': False,
        'rating': Decimal('4.5'),
        'total_sales': 134,
        'image_url': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Strawberry Masai',
        'description': 'Locally grown Limuru strawberries blended with a drizzle of raw acacia honey. Fresh, bright, and seasonal.',
        'price': Decimal('360.00'),
        'color_hex': '#FF6B8A',
        'category': 'fruity',
        'stock': 140,
        'is_featured': False,
        'rating': Decimal('4.7'),
        'total_sales': 198,
        'image_url': 'https://images.unsplash.com/photo-1633933358116-a27b902fad35?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Matcha Forest',
        'description': 'Ceremonial-grade Japanese matcha blended with sweetened condensed milk. Earthy, complex, beautiful.',
        'price': Decimal('520.00'),
        'color_hex': '#6D8B5F',
        'category': 'premium',
        'stock': 75,
        'is_featured': True,
        'rating': Decimal('4.8'),
        'total_sales': 167,
        'image_url': 'https://images.unsplash.com/photo-1582716401301-b2407dc7563d?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Lemon Zest Sherbet',
        'description': 'Bright East African lemons, a pinch of turmeric, and cane sugar make this a zingy palate cleanser.',
        'price': Decimal('330.00'),
        'color_hex': '#FFF176',
        'category': 'sorbet',
        'stock': 110,
        'is_dairy_free': True,
        'is_featured': False,
        'rating': Decimal('4.4'),
        'total_sales': 112,
        'image_url': 'https://images.unsplash.com/photo-1557142046-c704a3adf364?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Black Sesame Midnight',
        'description': 'Toasted black sesame paste swirled through premium cream. Deep, nutty, and hauntingly beautiful.',
        'price': Decimal('550.00'),
        'color_hex': '#1A1A2E',
        'category': 'premium',
        'stock': 60,
        'is_featured': False,
        'rating': Decimal('4.6'),
        'total_sales': 89,
        'image_url': 'https://images.unsplash.com/photo-1563699902328-8b82f9929c8e?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Avocado Dream',
        'description': 'Creamy Kenyan Hass avocado with a squeeze of lime and condensed milk. Rich, lush, and utterly unique.',
        'price': Decimal('440.00'),
        'color_hex': '#6DB356',
        'category': 'premium',
        'stock': 85,
        'is_dairy_free': False,
        'is_featured': False,
        'rating': Decimal('4.5'),
        'total_sales': 102,
        'image_url': 'https://images.unsplash.com/photo-1545249390-6bdfa286032f?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Rose & Cardamom Kulfi',
        'description': 'Inspired by South Asian kulfi — dense, slow-frozen with rose water, pistachios, and cardamom. A cultural gem.',
        'price': Decimal('500.00'),
        'color_hex': '#FFACC7',
        'category': 'premium',
        'stock': 70,
        'is_featured': True,
        'rating': Decimal('4.9'),
        'total_sales': 145,
        'image_url': 'https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&q=80&w=600',
    },
]

CATEGORIES = [
    {'name': 'Classic', 'slug': 'classic', 'icon': '🍦', 'description': 'Timeless, beloved flavors'},
    {'name': 'Fruity', 'slug': 'fruity', 'icon': '🍓', 'description': 'Fresh fruit bursts'},
    {'name': 'Sorbet & Dairy-Free', 'slug': 'sorbet', 'icon': '🌱', 'description': 'Vegan-friendly options'},
    {'name': 'Premium', 'slug': 'premium', 'icon': '✨', 'description': 'Chef\'s special selections'},
]

INVENTORY_ITEMS = [
    {'sku': 'DRY-001', 'name': 'Fresh Whole Milk', 'category': 'dairy', 'current_stock': 150, 'min_stock': 50, 'max_stock': 500, 'unit': 'Litres', 'unit_cost': 80},
    {'sku': 'DRY-002', 'name': 'Heavy Cream', 'category': 'dairy', 'current_stock': 80, 'min_stock': 30, 'max_stock': 200, 'unit': 'Litres', 'unit_cost': 250},
    {'sku': 'DRY-003', 'name': 'Condensed Milk', 'category': 'dairy', 'current_stock': 60, 'min_stock': 20, 'max_stock': 150, 'unit': 'Cans', 'unit_cost': 180},
    {'sku': 'SWT-001', 'name': 'Cane Sugar', 'category': 'sweetener', 'current_stock': 200, 'min_stock': 50, 'max_stock': 500, 'unit': 'Kg', 'unit_cost': 120},
    {'sku': 'SWT-002', 'name': 'Acacia Honey', 'category': 'sweetener', 'current_stock': 25, 'min_stock': 10, 'max_stock': 60, 'unit': 'Kg', 'unit_cost': 800},
    {'sku': 'FLV-001', 'name': 'Tahitian Vanilla Pods', 'category': 'flavoring', 'current_stock': 200, 'min_stock': 80, 'max_stock': 400, 'unit': 'Pods', 'unit_cost': 45},
    {'sku': 'FLV-002', 'name': 'Single-Origin Cocoa Powder', 'category': 'flavoring', 'current_stock': 30, 'min_stock': 15, 'max_stock': 80, 'unit': 'Kg', 'unit_cost': 950},
    {'sku': 'FLV-003', 'name': 'Ceremonial Matcha', 'category': 'flavoring', 'current_stock': 8, 'min_stock': 10, 'max_stock': 30, 'unit': 'Kg', 'unit_cost': 2800},
    {'sku': 'PKG-001', 'name': 'Branded Cups 500ml', 'category': 'packaging', 'current_stock': 1200, 'min_stock': 400, 'max_stock': 3000, 'unit': 'Units', 'unit_cost': 35},
    {'sku': 'PKG-002', 'name': 'Waffle Cones', 'category': 'packaging', 'current_stock': 800, 'min_stock': 300, 'max_stock': 2000, 'unit': 'Units', 'unit_cost': 25},
    {'sku': 'PKG-003', 'name': 'Dry Ice Blocks', 'category': 'packaging', 'current_stock': 40, 'min_stock': 20, 'max_stock': 100, 'unit': 'Kg', 'unit_cost': 600},
]


class Command(BaseCommand):
    help = 'Seed the database with sample Savanna Scoops data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🍦 Seeding Savanna Scoops database...'))

        # Site settings
        settings_obj, _ = SiteSettings.objects.get_or_create(pk=1)
        settings_obj.store_name = 'Savanna Scoops'
        settings_obj.tagline = 'Hand-Churned Since 2012'
        settings_obj.address = 'The Hub Karen, Nairobi'
        settings_obj.phone = '+254 700 123 456'
        settings_obj.email = 'hello@savanascoops.co.ke'
        settings_obj.delivery_fee = Decimal('150.00')
        settings_obj.free_delivery_threshold = Decimal('2000.00')
        settings_obj.save()
        self.stdout.write('  ✓ Site settings configured')

        # Categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            cat_map[cat_data['slug']] = cat
            if created:
                self.stdout.write(f'  ✓ Category: {cat.name}')

        # Flavors
        for f_data in FLAVORS:
            cat_slug = f_data.pop('category')
            cat = cat_map.get(cat_slug)
            flavor, created = Flavor.objects.get_or_create(
                name=f_data['name'],
                defaults={**f_data, 'category': cat}
            )
            if not created:
                for k, v in f_data.items():
                    setattr(flavor, k, v)
                flavor.category = cat
                flavor.save()
            if created:
                self.stdout.write(f'  ✓ Flavor: {flavor.name}')

        # Inventory items
        for inv_data in INVENTORY_ITEMS:
            item, created = InventoryItem.objects.get_or_create(
                sku=inv_data['sku'],
                defaults=inv_data
            )
            if created:
                self.stdout.write(f'  ✓ Inventory: {item.name}')

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@savanascoops.co.ke',
                password='admin123',
                first_name='Admin',
                last_name='Scoops',
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Superuser created: admin / admin123'))

        # Sample orders
        if Order.objects.count() == 0:
            flavors = list(Flavor.objects.all())
            for i in range(5):
                order = Order.objects.create(
                    customer_name=f'Customer {i+1}',
                    customer_email=f'customer{i+1}@example.com',
                    customer_phone=f'+2547{random.randint(10000000, 99999999)}',
                    delivery_address=f'{random.choice(["Karen", "Westlands", "Kilimani", "Lavington"])} Nairobi',
                    subtotal=Decimal(str(random.randint(500, 2000))),
                    delivery_fee=Decimal('150.00'),
                    total=Decimal(str(random.randint(650, 2150))),
                    status=random.choice(['delivered', 'confirmed', 'preparing']),
                    payment_status='paid' if random.random() > 0.2 else 'pending',
                )
                if flavors:
                    flavor = random.choice(flavors)
                    OrderItem.objects.create(
                        order=order,
                        flavor=flavor,
                        flavor_name=flavor.name,
                        price=flavor.price,
                        quantity=random.randint(1, 3),
                    )
            self.stdout.write('  ✓ 5 sample orders created')

        self.stdout.write(self.style.SUCCESS('\n✅ Savanna Scoops database seeded successfully!'))
        self.stdout.write(self.style.WARNING('   Admin login: admin / admin123'))
        self.stdout.write(self.style.WARNING('   Admin panel: http://127.0.0.1:8000/admin-panel/'))
        self.stdout.write(self.style.WARNING('   Django admin: http://127.0.0.1:8000/django-admin/'))
