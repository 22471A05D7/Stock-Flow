from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Shared Bootstrap 5 styling for every input inside our forms.
_INPUT_ATTRS = {'class': 'form-control'}


class SignupForm(forms.Form):
    """
    Fields exactly as required: Email, Password, Confirm Password,
    Organization Name.

    NOTE: we log users in with their EMAIL as the account username,
    so "email" is never stored as a plain extra identifier -- the
    User table's username column IS the email (lower-cased).
    """

    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            **_INPUT_ATTRS,
            'placeholder': 'you@company.com',
            'autofocus': 'autofocus',
        }),
    )

    organization_name = forms.CharField(
        label='Organization Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            **_INPUT_ATTRS,
            'placeholder': 'e.g. Acme Traders',
        }),
    )

    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            **_INPUT_ATTRS,
            'placeholder': 'At least 8 characters',
        }),
    )

    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            **_INPUT_ATTRS,
            'placeholder': 'Repeat the password',
        }),
    )

    def clean_email(self):
        """Case-insensitive duplicate email check (real DB check)."""
        email = self.cleaned_data['email'].strip().lower()
        if (
            User.objects.filter(username__iexact=email).exists()
            or User.objects.filter(email__iexact=email).exists()
        ):
            raise forms.ValidationError(
                'An account with this email already exists. Please log in instead.'
            )
        return email

    def clean(self):
        """
        Field-combination checks:
        1. Both passwords match.
        2. Password passes Django's configured validation rules
           (minimum 8 characters, not too common/similar/numeric only).
        """
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match. Please try again.')
        elif password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error('password2', exc.messages)

        return cleaned


class LoginForm(forms.Form):
    """
    Simple login form accepting the email as the username.

    (We use a light custom form instead of Django's AuthenticationForm
    so we fully control the placeholder text and error styling.)
    """

    username = forms.CharField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            **_INPUT_ATTRS,
            'placeholder': 'you@company.com',
            'autofocus': 'autofocus',
        }),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            **_INPUT_ATTRS,
            'placeholder': 'Your password',
        }),
    )

    error_messages = {
        'invalid_login': "No matching account for this email and password.",
    }
