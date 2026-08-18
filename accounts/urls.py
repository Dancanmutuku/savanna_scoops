from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.profile_view,
        name="profile",
    ),

    path(
        "google/onboarding/",
        views.google_onboarding_view,
        name="google_onboarding",
    ),

    path(
        "google/onboarding/complete/",
        views.google_onboarding_complete,
        name="google_onboarding_complete",
    ),

    path(
        "<str:username>/",
        views.profile_view,
        name="profile_detail",
    ),
]