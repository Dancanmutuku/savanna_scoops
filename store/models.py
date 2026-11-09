from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils.text import slugify


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
        'image_url': 'https://images.unsplash.com/photo-1715194803865-54f4358f87ef?auto=format&fit=crop&q=80&w=600',
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
        'image_url': 'https://images.unsplash.com/photo-1627222295124-f8b3fc09e47f?auto=format&fit=crop&q=80&w=600',
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
        'image_url': 'https://images.unsplash.com/photo-1597249536924-b226b1a1259d?auto=format&fit=crop&q=80&w=600',
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


def ensure_default_catalog():
    if Category.objects.count() >= len(DEFAULT_CATEGORIES) and Flavor.objects.count() >= len(DEFAULT_FLAVORS):
        return

    for category_data in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            slug=category_data['slug'],
            defaults=category_data,
        )

    category_map = {category.slug: category for category in Category.objects.all()}
    for flavor_data in DEFAULT_FLAVORS:
        category = category_map.get(flavor_data['category'])
        if category is None:
            continue

        defaults = {key: value for key, value in flavor_data.items() if key != 'category'}
        defaults['category'] = category
        flavor, created = Flavor.objects.get_or_create(
            name=flavor_data['name'],
            defaults=defaults,
        )
        if not created:
            for key, value in defaults.items():
                setattr(flavor, key, value)
            flavor.save()


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        cache.delete('store:categories')


class Flavor(models.Model):
    STATUS_CHOICES = [
        ('high', 'High Stock'),
        ('low', 'Low Stock'),
        ('out', 'Out of Stock'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='flavors/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='flavors')
    stock = models.PositiveIntegerField(default=100)
    min_stock = models.PositiveIntegerField(default=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='high')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    total_sales = models.PositiveIntegerField(default=0)
    color_hex = models.CharField(max_length=7, default='#F3E5AB')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)
    allergens = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-total_sales']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Auto-update status
        if self.stock == 0:
            self.status = 'out'
        elif self.stock <= self.min_stock:
            self.status = 'low'
        else:
            self.status = 'high'
        super().save(*args, **kwargs)
        cache.delete('store:flavors:active')

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url

    @property
    def stock_percentage(self):
        if self.min_stock * 2 == 0:
            return 100
        return min(100, int((self.stock / (self.min_stock * 2)) * 100))


class Review(models.Model):
    flavor = models.ForeignKey(Flavor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['flavor', 'user']

    def __str__(self):
        return f'{self.user.email} - {self.flavor.name} (rating {self.rating}/5)'


class SiteSettings(models.Model):
    store_name = models.CharField(max_length=200, default='Savanna Scoops')
    tagline = models.CharField(max_length=300, default='Hand-Churned Since 2012')
    address = models.CharField(max_length=500, default='Westlands, Nairobi')
    phone = models.CharField(max_length=20, default='+254 700 000 000')
    email = models.EmailField(default='hello@savanascoops.com')
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=150)
    free_delivery_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=2000)
    hero_image_url = models.URLField(blank=True, default='https://images.unsplash.com/photo-1549395156-e0c1fe6fc7a5?auto=format&fit=crop&q=80&w=2000')
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.store_name

    @classmethod
    def get_settings(cls):
        obj = cache.get('store:site-settings')
        if obj:
            return obj
        obj, _ = cls.objects.get_or_create(pk=1)
        cache.set('store:site-settings', obj, 300)
        return obj

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('store:site-settings')
