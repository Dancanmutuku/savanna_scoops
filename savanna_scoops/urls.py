from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('store.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('admin-panel/', include('inventory.admin_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
