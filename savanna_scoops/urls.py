from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('django-admin/', RedirectView.as_view(url='/admin/', permanent=False)),
    path('accounts/login/', account_views.login_view, name='account_login'),
    path('accounts/signup/', account_views.register_view, name='account_signup'),
    path('accounts/', include('allauth.urls')),
    path('profile/', include('accounts.urls')),
    path('', include('store.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('inventory/', include('inventory.urls')),
    path('admin-panel/', include('inventory.admin_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
