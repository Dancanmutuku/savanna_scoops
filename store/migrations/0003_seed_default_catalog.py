from decimal import Decimal

from django.db import migrations


DEFAULT_CATEGORIES = [
    {'name': 'Classic', 'slug': 'classic', 'description': 'Timeless, beloved flavors'},
    {'name': 'Fruity', 'slug': 'fruity', 'description': 'Fresh fruit bursts'},
    {'name': 'Sorbet & Dairy-Free', 'slug': 'sorbet', 'description': 'Vegan-friendly options'},
    {'name': 'Premium', 'slug': 'premium', 'description': "Chef's special selections"},
]

DEFAULT_FLAVORS = [
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
    {
        'name': 'Blueberry Ripple',
        'description': 'Blueberry compote folded into vanilla cream with a gentle swirl of lemon curd. Bright, juicy, and crowd-pleasing.',
        'price': Decimal('390.00'),
        'color_hex': '#5376D8',
        'category': 'fruity',
        'stock': 135,
        'is_featured': False,
        'rating': Decimal('4.7'),
        'total_sales': 176,
        'image_url': 'https://images.unsplash.com/photo-1519996521430-02b4d6cb0af4?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Cinnamon Swirl Crunch',
        'description': 'Warm cinnamon-spiced cream layered with caramelized biscuit crumbs for a cozy, bakery-inspired finish.',
        'price': Decimal('410.00'),
        'color_hex': '#B9793F',
        'category': 'classic',
        'stock': 125,
        'is_featured': True,
        'rating': Decimal('4.8'),
        'total_sales': 203,
        'image_url': 'https://images.unsplash.com/photo-1505253716362-afaea1a3d1af?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Pistachio Rose Cloud',
        'description': 'Silky pistachio cream with a floral rose finish and crunchy pistachio praline. Light but indulgent.',
        'price': Decimal('470.00'),
        'color_hex': '#8DBA83',
        'category': 'premium',
        'stock': 78,
        'is_featured': False,
        'rating': Decimal('4.8'),
        'total_sales': 164,
        'image_url': 'https://images.unsplash.com/photo-1528825871115-3581a5387919?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Coconut Lime Chill',
        'description': 'A vibrant, zero-dairy scoop of coconut cream and lime zest with a clean tropical finish.',
        'price': Decimal('370.00'),
        'color_hex': '#D9E77B',
        'category': 'sorbet',
        'stock': 145,
        'is_dairy_free': True,
        'is_featured': True,
        'rating': Decimal('4.7'),
        'total_sales': 187,
        'image_url': 'https://images.unsplash.com/photo-1553530666-ba11a7da3888?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Peach & Ginger Glow',
        'description': 'Ripe peach purée balanced with ginger syrup and a touch of vanilla. Bright, fragrant, and mellow.',
        'price': Decimal('385.00'),
        'color_hex': '#F5AF5D',
        'category': 'fruity',
        'stock': 130,
        'is_featured': False,
        'rating': Decimal('4.6'),
        'total_sales': 143,
        'image_url': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&q=80&w=600',
    },
    {
        'name': 'Nairobi Berry Cheesecake',
        'description': 'Creamy cheesecake-inspired base with berry swirls, crushed biscuits, and a satin-smooth texture.',
        'price': Decimal('495.00'),
        'color_hex': '#D174A3',
        'category': 'premium',
        'stock': 72,
        'is_featured': True,
        'rating': Decimal('4.9'),
        'total_sales': 221,
        'image_url': 'https://images.unsplash.com/photo-1486427944299-d1955d23e34d?auto=format&fit=crop&q=80&w=600',
    },
]


def seed_default_catalog(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Flavor = apps.get_model('store', 'Flavor')

    if Category.objects.count() >= len(DEFAULT_CATEGORIES) and Flavor.objects.count() >= len(DEFAULT_FLAVORS):
        return

    for category_data in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(slug=category_data['slug'], defaults=category_data)

    category_map = {category.slug: category for category in Category.objects.all()}
    for flavor_data in DEFAULT_FLAVORS:
        category = category_map.get(flavor_data['category'])
        if category is None:
            continue

        defaults = {key: value for key, value in flavor_data.items() if key != 'category'}
        defaults['category_id'] = category.pk
        flavor, created = Flavor.objects.get_or_create(name=flavor_data['name'], defaults=defaults)
        if not created:
            for key, value in defaults.items():
                setattr(flavor, key, value)
            flavor.save()


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_remove_category_icon'),
    ]

    operations = [
        migrations.RunPython(seed_default_catalog, migrations.RunPython.noop),
    ]
