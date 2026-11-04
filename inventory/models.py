from django.db import models

from accounts.models import Organization


class Product(models.Model):
    """
    A single product in an organization's inventory.

    Every query, update and delete on Product MUST start from the
    parent Organization -- that is what guarantees user A can never
    see or change user B's data. See views in this app for examples.
    """

    # Each product belongs to one organization; deleting the
    # organization removes all of its products (on_delete=CASCADE).
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products',
    )

    name = models.CharField(
        'Product Name',
        max_length=150,
    )

    # Stock Keeping Unit -- a short unique code per product.
    # The uniqueness scope is enforced at DATABASE level below:
    # the same SKU can exist in different organizations, but not
    # twice inside the same one.
    sku = models.CharField(
        'SKU',
        max_length=64,
    )

    # Optional free text. blank=True means it may stay empty in forms;
    # default='' keeps the column non-null in the database.
    description = models.TextField(
        'Description',
        blank=True,
        default='',
    )

    # Units currently in stock. Never negative.
    quantity = models.PositiveIntegerField(
        'Quantity on Hand',
        default=0,
    )

    # Prices use DecimalField (NOT FloatField) so money values are
    # stored exactly. 12 digits total, 2 after the decimal point.
    cost_price = models.DecimalField(
        'Cost Price',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    selling_price = models.DecimalField(
        'Selling Price',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # Per-product threshold. Optional: an empty value means
    # "fall back to the organization's default threshold".
    # null=True lets the DATABASE store "no value";
    # blank=True lets FORMS leave it empty.
    low_stock_threshold = models.PositiveIntegerField(
        'Low Stock Threshold',
        null=True,
        blank=True,
    )

    # auto_now_add = set once, when the row is FIRST created.
    created_at = models.DateTimeField(
        'Created At',
        auto_now_add=True,
    )

    # auto_now = refreshed automatically on EVERY save/update.
    updated_at = models.DateTimeField(
        'Updated At',
        auto_now=True,
    )

    class Meta:
        ordering = ['-created_at']  # newest products first in all lists

        constraints = [
            # Ask the REAL database to reject duplicate SKUs per org.
            # This stays true even if we later switch to PostgreSQL.
            models.UniqueConstraint(
                fields=['organization', 'sku'],
                name='unique_sku_per_organization',
            ),
            # Extra DB-level safety against negative money values.
            models.CheckConstraint(
                condition=models.Q(cost_price__gte=0),
                name='cost_price_non_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(selling_price__gte=0),
                name='selling_price_non_negative',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def is_low_stock(self):
        """
        Low-stock rule: quantity on hand <= low stock threshold.
        When this product has no threshold of its own, fall back to
        the owning organization's default threshold.
        """
        threshold = self.effective_threshold()
        return self.quantity <= threshold

    def is_out_of_stock(self):
        return self.quantity == 0

    def effective_threshold(self):
        """Return the threshold actually used for low-stock checks."""
        if self.low_stock_threshold is not None:
            return self.low_stock_threshold
        return self.organization.default_low_stock_threshold
