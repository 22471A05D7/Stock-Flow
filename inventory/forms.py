from django import forms


from .models import Product


class SettingsForm(forms.Form):
    """
    Organization settings:
    - rename the organization
    - set the DEFAULT low stock threshold used by every product
      whose own threshold is empty.
    """

    organization_name = forms.CharField(
        label='Organization Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }),
    )

    default_low_stock_threshold = forms.IntegerField(
        label='Default Low Stock Threshold',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )


class ProductForm(forms.Form):
    """
    Shared by Add Product and Edit Product.

    Includes validation for:
    - required fields (name, sku)
    - quantity >= 0, prices >= 0
    - SKU unique WITHIN the caller's organization.

    The organization and (when editing) the current product are
    injected via __init__ so validation can be scoped correctly.
    """

    name = forms.CharField(
        label='Product Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Steel Bolt M8',
        }),
    )

    sku = forms.CharField(
        label='SKU',
        max_length=64,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. BOLT-M8-100',
        }),
    )

    description = forms.CharField(
        label='Description (optional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Short description, supplier notes, etc.',
        }),
    )

    quantity = forms.IntegerField(
        label='Quantity on Hand',
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    cost_price = forms.DecimalField(
        label='Cost Price',
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )

    selling_price = forms.DecimalField(
        label='Selling Price',
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )

    low_stock_threshold = forms.IntegerField(
        label='Low Stock Threshold',
        min_value=0,
        required=False,
        help_text='Leave empty to use your organization\'s default threshold.',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, organization=None, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.product = product  # set when EDITING an existing product

        # Autofill a sensible selling price suggestion? No -- keep it simple;
        # the fields carry the DB values themselves via the views.

    def clean_sku(self):
        """SKU must be unique inside THIS organization (DB-backed check)."""
        sku = self.cleaned_data['sku'].strip().upper()
        if not sku:
            raise forms.ValidationError('SKU is required.')

        queryset = Product.objects.filter(
            organization=self.organization,
            sku__iexact=sku,
        )
        if self.product is not None:
            queryset = queryset.exclude(pk=self.product.pk)

        if queryset.exists():
            raise forms.ValidationError(
                'This SKU is already used by another product in your organization.'
            )
        return sku

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Product name is required.')
        return name
