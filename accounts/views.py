from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.urls import get_resolver
from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get('password1')
        p2 = data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next') or '/'

    if request.user.is_authenticated:
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            if not next_url.startswith('/admin-panel/') or request.user.is_staff:
                return redirect(next_url)
            messages.error(request, 'Staff access is required for the admin panel.')
        return redirect('shop')
    
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=identifier, password=password)
        
        if user:
            login(request, user)
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('shop')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    google_app = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {})
    google_enabled = bool(google_app.get('client_id') and google_app.get('secret'))
    if google_enabled:
        try:
            from allauth.socialaccount.providers.google import urls as google_urls  # noqa: F401
            reverse_dict = get_resolver().reverse_dict
            google_enabled = any(
                isinstance(name, str) and name.startswith('google_')
                for name in reverse_dict.keys()
            )
        except Exception:
            google_enabled = False
    return render(
        request,
        'accounts/login.html',
        {
            'next': next_url,
            'google_enabled': google_enabled,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('shop')
    
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Welcome to Savanna Scoops, {user.first_name}!')
        return redirect('shop')
    
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('shop')


@login_required
def profile_view(request, username=None):
    from orders.models import Order
    if username and username not in {request.user.username, request.user.email}:
        messages.error(request, 'You can only view your own profile.')
        return redirect('profile')
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()
        messages.success(request, 'Profile updated!')
    orders = Order.objects.filter(user=request.user).prefetch_related('items')[:10]
    return render(request, 'accounts/profile.html', {'orders': orders})
