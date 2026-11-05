from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        label="Full name",
    )
    phone = forms.CharField(
        max_length=15,
        label="Phone number",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "phone",
            "password1",
            "password2",
        ]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if Profile.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "An account with this phone number already exists."
            )

        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"]

        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
            )

        return user
