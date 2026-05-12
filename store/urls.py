from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('flavor/<slug:slug>/', views.flavor_detail, name='flavor_detail'),
    path('cart/', views.cart_view, name='cart_api'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('tracking/', views.tracking, name='tracking'),
    path('review/<slug:slug>/', views.submit_review, name='submit_review'),
]
