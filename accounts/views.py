from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View

from .forms import LoginForm, SignupForm
from .models import Organization


class SignupView(View):
    """
    GET  -> show the empty signup form.
    POST -> validate + create User AND Organization in ONE atomic
    database transaction, log the user in, go to the dashboard.

    If any database step fails midway, nothing is saved at all --
    no half-created users or organizations.
    """

    template_name = 'accounts/signup.html'

    def get(self, request):
        # Already logged in? No point showing signup again.
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name, {'form': SignupForm()})

    def post(self, request):
        form = SignupForm(request.POST)
        if not form.is_valid():
            # Re-render with the exact validation messages.
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email'].strip().lower()

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=form.cleaned_data['password1'],
                )
                organization = Organization.objects.create(
                    name=form.cleaned_data['organization_name'].strip(),
                    owner=user,
                    # default_low_stock_threshold uses the model default (5)
                )
        except ValidationError as exc:
            # Defensive: password validators firing again (e.g. race).
            form.add_error('password2', exc.messages)
            return render(request, self.template_name, {'form': form})

        # Log them in immediately -- instant entry to the app.
        login(request, user)
        messages.success(
            request,
            f'Welcome to StockFlow! Your organization "{organization.name}" is ready.',
        )
        return redirect('dashboard')


class LoginView(View):
    """
    GET  -> show the login form.
    POST -> authenticate against the REAL users database table.
    """

    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        user = authenticate(
            request,
            username=form.cleaned_data['username'].strip().lower(),
            password=form.cleaned_data['password'],
        )
        if user is None:
            # Generic message: never reveal which part was wrong.
            form.add_error(None, 'Invalid email or password. Please try again.')
            return render(request, self.template_name, {'form': form})

        login(request, user)
        messages.success(request, f'Welcome back, {user.organization.name}!')
        return redirect('dashboard')


class LogoutView(View):
    """Logout requires POST (safer than GET). The sidebar sends a POST form."""

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('login')
