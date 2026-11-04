from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import get_user_organization
from .forms import ProductForm, SettingsForm
from .models import Product


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _clean_org(request):
    """
    Return the logged-in user's organization, or None when it's missing.

    None means: session/user exists but has no org row (edge case) --
    we force a fresh login instead of showing data or a confusing error.
    """
    org = get_user_organization(request.user)
    if org is None:
        messages.error(request, 'Unable to load your organization. Please log in again.')
    return org


# ---------------------------------------------------------------------------
# Dashboard & Settings  (settings: real implementation comes in Phase 6)
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    org = _clean_org(request)
    if org is None:
        return redirect('login')

    # EVERY dashboard query starts from this user's organization only.
    products = Product.objects.filter(organization=org)

    # --- Summary numbers ---------------------------------------------------
    total_products = products.count()

    units_result = products.aggregate(total=Coalesce(Sum('quantity'), 0))
    total_units = units_result['total']

    # Low stock = quantity <= threshold, where the threshold is:
    #   the product's OWN threshold when set,
    #   otherwise the organization's default threshold.
    # Done in the DATABASE for speed (F() references the column itself).
    low_items = products.filter(
        Q(low_stock_threshold__isnull=False,
          quantity__lte=F('low_stock_threshold'))
        |
        Q(low_stock_threshold__isnull=True,
          quantity__lte=org.default_low_stock_threshold)
    ).order_by('quantity', 'name')

    out_items = products.filter(quantity=0).order_by('name')

    return render(request, 'inventory/dashboard.html', {
        'total_products': total_products,
        'total_units': total_units,
        'low_items': low_items,
        'out_items': out_items,
        'org_default_threshold': org.default_low_stock_threshold,
    })


@login_required
def settings(request):
    org = _clean_org(request)
    if org is None:
        return redirect('login')

    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            org.name = form.cleaned_data['organization_name'].strip()
            org.default_low_stock_threshold = form.cleaned_data[
                'default_low_stock_threshold'
            ]
            org.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('settings')
    else:
        form = SettingsForm(initial={
            'organization_name': org.name,
            'default_low_stock_threshold': org.default_low_stock_threshold,
        })

    return render(request, 'inventory/settings.html', {'form': form})


# ---------------------------------------------------------------------------
# Product listing + search
# ---------------------------------------------------------------------------

@login_required
def product_list(request):
    org = _clean_org(request)
    if org is None:
        return redirect('login')

    query = request.GET.get('q', '').strip()
    # EVERY product query is scoped to this user's organization.
    products = Product.objects.filter(organization=org)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

    products = products.order_by('name')

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'query': query,
        'total_count': Product.objects.filter(organization=org).count(),
    })


# ---------------------------------------------------------------------------
# Add product
# ---------------------------------------------------------------------------

@login_required
def product_add(request):
    org = _clean_org(request)
    if org is None:
        return redirect('login')

    if request.method == 'POST':
        form = ProductForm(request.POST, organization=org)
        if form.is_valid():
            data = form.cleaned_data
            Product.objects.create(
                organization=org,
                name=data['name'],
                sku=data['sku'],
                description=data['description'],
                quantity=data['quantity'],
                cost_price=data['cost_price'],
                selling_price=data['selling_price'],
                low_stock_threshold=data['low_stock_threshold'],
            )
            messages.success(request, f'Product "{data["name"]}" was added.')
            return redirect('products')
    else:
        form = ProductForm()

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'is_edit': False,
    })


# ---------------------------------------------------------------------------
# Edit product
# ---------------------------------------------------------------------------

@login_required
def product_edit(request, pk):
    org = _clean_org(request)
    if org is None:
        return redirect('login')

    # Scoped lookup: a product id from ANOTHER organization hits a 404.
    product = get_object_or_404(Product, pk=pk, organization=org)

    if request.method == 'POST':
        form = ProductForm(request.POST, organization=org, product=product)
        if form.is_valid():
            data = form.cleaned_data
            product.name = data['name']
            product.sku = data['sku']
            product.description = data['description']
            product.quantity = data['quantity']
            product.cost_price = data['cost_price']
            product.selling_price = data['selling_price']
            product.low_stock_threshold = data['low_stock_threshold']
            product.save()
            messages.success(request, f'Product "{product.name}" was updated.')
            return redirect('products')
    else:
        form = ProductForm(
            initial={
                'name': product.name,
                'sku': product.sku,
                'description': product.description,
                'quantity': product.quantity,
                'cost_price': product.cost_price,
                'selling_price': product.selling_price,
                'low_stock_threshold': product.low_stock_threshold,
            },
            organization=org,
            product=product,
        )

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'is_edit': True,
        'product': product,
    })


# ---------------------------------------------------------------------------
# Delete product (POST only, with client-side confirmation modal)
# ---------------------------------------------------------------------------

@login_required
def product_delete(request, pk):
    org = _clean_org(request)
    if org is None:
        return redirect('login')

    if request.method != 'POST':
        # Deletion must never happen through a plain link/bot GET.
        return redirect('products')

    product = get_object_or_404(Product, pk=pk, organization=org)
    name = product.name
    product.delete()
    messages.success(request, f'Product "{name}" was deleted.')
    return redirect('products')
