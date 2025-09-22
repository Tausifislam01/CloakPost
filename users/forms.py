from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    """
    Creates a user, sets password, generates RSA keypair,
    and stores encrypted private key using a password-derived AES key.
    Ensures the user is saved first to get a real id for AAD.
    """
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ["username", "email"]

    def clean(self):
        data = super().clean()
        p1 = data.get("password1")
        p2 = data.get("password2")
        if not p1 or not p2 or p1 != p2:
            raise ValidationError("Passwords do not match.")
        if len(p1) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        return data

    def save(self, commit: bool = True) -> CustomUser:
        user: CustomUser = super().save(commit=False)
        password = self.cleaned_data["password1"]
        user.set_password(password)
        user.set_kdf_salt()

        if commit:
            # 1) Save first to ensure we have a primary key for AAD
            user.save()
            # 2) Now generate RSA and store encrypted private key (AAD includes uid)
            user.generate_rsa_and_store(password)
            # 3) Persist the key fields
            user.save(update_fields=["public_key", "encrypted_private_key", "kdf_salt", "password"])
        else:
            # Fallback path (rare): generate keys without a pk in AAD (uses uid=-1)
            user.generate_rsa_and_store(password)

        return user


class LoginForm(AuthenticationForm):
    """
    Uses Django's built-in auth validation.
    """
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)