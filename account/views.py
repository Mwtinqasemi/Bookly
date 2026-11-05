from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    LogoutView as DjangoLogoutView,
)
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("reserve:home")

    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("reserve:home")
    else:
        form = RegisterForm()

    return render(
        request,
        "account/register.html",
        {
            "form": form,
            "next": next_url,
        },
    )


class LoginView(DjangoLoginView):
    template_name = "account/login.html"
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    next_page = "reserve:home"
