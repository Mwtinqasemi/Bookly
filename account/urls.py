from django.urls import path

from .views import LoginView, LogoutView, register_view


app_name = "account"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "register/",
        register_view,
        name="register",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
]
