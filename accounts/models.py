from django.contrib.auth.models import User
from django.db import models


class Organization(models.Model):
    """
    A company/team that owns its products.

    Key rules:
    - Every Organization belongs to exactly one owner (see OneToOneField below).
    - Every Product belongs to exactly one Organization (see Product model).
    - ALL data isolation between users is achieved by always filtering
      products through the Organization that belongs to the logged-in user.
    """

    # Organization name, e.g. "Acme Traders". Required field.
    name = models.CharField(
        'Organization Name',
        max_length=150,
    )

    # One-to-one link: one user owns exactly one organization, and
    # deleting the user deletes their organization (on_delete=CASCADE).
    # We can then access it like: user.organization
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='organization',
        verbose_name='Owner',
    )

    # Fallback threshold used for products whose own threshold is empty.
    # PositiveIntegerField never accepts negative numbers.
    default_low_stock_threshold = models.PositiveIntegerField(
        'Default Low Stock Threshold',
        default=5,
    )

    # Set automatically the first time the record is saved.
    created_at = models.DateTimeField(
        'Created At',
        auto_now_add=True,
    )

    def __str__(self):
        """Human-readable name in the admin and shell."""
        return self.name
