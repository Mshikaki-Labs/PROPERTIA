from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from invoices.models import Invoice, InvoicePayment
from payments.models import Payment
from .views import sync_user_arrears


@receiver(pre_save, sender=Invoice)
def _cache_invoice_old_values(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Invoice.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_due_date = old.due_date
        except Invoice.DoesNotExist:
            pass


@receiver(post_save, sender=Invoice)
def _sync_arrears_on_invoice_save(sender, instance, created, **kwargs):
    if created or getattr(instance, '_old_status', None) != instance.status or getattr(instance, '_old_due_date', None) != instance.due_date:
        if instance.user:
            sync_user_arrears(instance.user)


@receiver(post_delete, sender=Invoice)
def _sync_arrears_on_invoice_delete(sender, instance, **kwargs):
    if instance.user:
        sync_user_arrears(instance.user)


@receiver(post_save, sender=InvoicePayment)
def _sync_arrears_on_invoice_payment_save(sender, instance, created, **kwargs):
    if instance.invoice and instance.invoice.user:
        sync_user_arrears(instance.invoice.user)


@receiver(post_delete, sender=InvoicePayment)
def _sync_arrears_on_invoice_payment_delete(sender, instance, **kwargs):
    if instance.invoice and instance.invoice.user:
        sync_user_arrears(instance.invoice.user)


@receiver(pre_save, sender=Payment)
def _cache_payment_old_values(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Payment.objects.get(pk=instance.pk)
            instance._old_balance = old.balance
        except Payment.DoesNotExist:
            pass


@receiver(post_save, sender=Payment)
def _sync_arrears_on_payment_save(sender, instance, created, **kwargs):
    if created or getattr(instance, '_old_balance', None) != instance.balance:
        if instance.user:
            sync_user_arrears(instance.user)


@receiver(post_delete, sender=Payment)
def _sync_arrears_on_payment_delete(sender, instance, **kwargs):
    if instance.user:
        sync_user_arrears(instance.user)
