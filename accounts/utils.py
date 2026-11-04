from .models import Organization


def get_user_organization(user):
    """
    Resolve the Organization that belongs to this user.

    This is THE single entry point for data isolation: inventory
    views call it and then filter/query products exclusively
    through the returned organization. A URL-provided or
    attacker-crafted organization id is never trusted.

    Returns None when the user has no organization (edge case:
    staff/other users created outside our signup flow).
    """
    try:
        return user.organization
    except Organization.DoesNotExist:
        return None
