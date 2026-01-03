from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_view, name="landing"),

    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("detail/", views.detail, name="detail"),
    path("delete/<int:asset_id>/", views.delete_asset, name="delete_asset"),
]