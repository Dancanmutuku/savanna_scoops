from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='🍦')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
        return f'{self.user.email} - {self.flavor.name} ({self.rating}★)'


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
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
