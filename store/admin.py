from django.contrib import admin
from .models import Flavor, Category, Review, SiteSettings


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'status', 'is_active', 'is_featured']
    list_filter = ['category', 'status', 'is_active', 'is_featured']
    list_editable = ['price', 'stock', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'flavor', 'rating', 'created_at']
    list_filter = ['rating']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    pass
