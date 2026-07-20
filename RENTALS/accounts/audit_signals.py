from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone

from .models import AuditLog
from .audit import get_current_user, get_current_ip

AUDITED_APPS = [
    'properties',
    'units',
    'tenants',
    'maintenance',
    'payments',
    'invoices',
    'leases',
    'water_bills',
    'arrears',
]


def _get_model_label(instance):
    return f"{instance._meta.app_label}.{instance._meta.model_name}"


def _get_changes(instance):
    original = getattr(instance, '_original_state', None)
    if original is None:
        return None
    current = model_to_dict(instance)
    changes = {}
    for field, old_value in original.items():
        new_value = current.get(field)
        if old_value != new_value:
            changes[field] = [str(old_value), str(new_value)]
    return changes or None


def _log_action(action, instance, changes=None):
    user = get_current_user()
    ip = get_current_ip()
    if action != AuditLog.ACTION_DELETE and not user:
        return
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=_get_model_label(instance),
        object_id=str(instance.pk),
        object_repr=str(instance),
        ip_address=ip,
        changes=changes,
    )


def _cache_original_state(sender, instance, **kwargs):
    if kwargs.get('raw', False):
        return
    if hasattr(instance, '_original_state'):
        return
    if not instance.pk:
        instance._original_state = {}
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._original_state = model_to_dict(old_instance)
    except sender.DoesNotExist:
        instance._original_state = {}


def _handle_save(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        _log_action(AuditLog.ACTION_CREATE, instance)
    else:
        changes = _get_changes(instance)
        if changes:
            _log_action(AuditLog.ACTION_UPDATE, instance, changes=changes)
    if hasattr(instance, '_original_state'):
        del instance._original_state


def _handle_delete(sender, instance, **kwargs):
    _log_action(AuditLog.ACTION_DELETE, instance)


def connect_audit_signals():
    from django.apps import apps
    for model in apps.get_models():
        if model._meta.app_label not in AUDITED_APPS:
            continue
        if model.__name__ == 'AuditLog':
            continue
        pre_save.connect(_cache_original_state, sender=model, weak=False)
        post_save.connect(_handle_save, sender=model, weak=False)
        pre_delete.connect(_handle_delete, sender=model, weak=False)
