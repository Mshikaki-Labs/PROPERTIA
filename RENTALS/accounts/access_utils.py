from django.db.models import Q
from properties.models import Property


def get_accessible_properties(user):
    """Return properties the user owns OR has been granted access to.
    Admins and landlords can access all properties when they have no owned/granted access."""
    accessible = Property.objects.filter(
        Q(user=user) | Q(granted_accesses__user=user)
    ).distinct()
    if accessible.exists():
        return accessible
    if user.is_authenticated:
        try:
            from .models import Profile
            if user.profile.role in [Profile.ADMIN, Profile.LANDLORD]:
                return Property.objects.all()
        except (Profile.DoesNotExist, AttributeError):
            pass
    return Property.objects.none()


def has_property_access(user, property_obj):
    """Check if a user can access a specific property."""
    if property_obj.user == user:
        return True
    return Property.objects.filter(
        pk=property_obj.pk,
        granted_accesses__user=user,
    ).exists()


def can_manage_properties(user):
    """Admins and property owners can write data; granted users can view/interact."""
    if not user.is_authenticated:
        return False
    try:
        from .models import Profile
        return user.profile.role in [Profile.ADMIN, Profile.LANDLORD]
    except (Profile.DoesNotExist, AttributeError):
        return False


def filter_units_by_accessible_properties(user, unit_queryset):
    """Filter a Unit queryset to only units in accessible properties."""
    prop_ids = get_accessible_properties(user).values_list('pk', flat=True)
    return unit_queryset.filter(property_id__in=prop_ids)


def filter_tenants_by_accessible_properties(user, tenant_queryset):
    """Filter a Tenant queryset to only tenants in accessible properties."""
    prop_ids = get_accessible_properties(user).values_list('pk', flat=True)
    return tenant_queryset.filter(unit__property_id__in=prop_ids)
