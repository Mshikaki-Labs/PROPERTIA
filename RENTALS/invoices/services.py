from decimal import Decimal

from django.db import transaction

from .models import Invoice, InvoicePayment
from payments.models import Payment


RENT_TYPE = 'Rent'


def _money(value):
    return Decimal(value or 0)


def set_payment_status_from_balance(payment):
    payment.status = 'claimed' if _money(payment.balance) <= 0 else 'unclaimed'
    payment.save(update_fields=['balance', 'status'])


def _apply_payment_to_invoice(payment, invoice, amount):
    amount = _money(amount)
    if amount <= 0:
        return None

    invoice_payment, created = InvoicePayment.objects.get_or_create(
        invoice=invoice,
        payment=payment,
        defaults={'amount_applied': amount},
    )
    if not created:
        return None

    payment.balance = _money(payment.balance) - amount
    set_payment_status_from_balance(payment)
    invoice.update_status()
    return invoice_payment


@transaction.atomic
def allocate_payment_to_rent_invoices(payment):
    """
    Apply a payment's remaining balance to the tenant's oldest open rent invoices.
    Any excess stays on payment.balance as tenant credit.
    """
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if _money(payment.balance) <= 0:
        return []

    allocations = []
    invoices = Invoice.objects.filter(
        user=payment.user,
        tenant=payment.tenant,
        type=RENT_TYPE,
    ).exclude(status='Paid').order_by('due_date', 'id')

    for invoice in invoices:
        remaining = _money(invoice.get_remaining_balance())
        if remaining <= 0:
            invoice.update_status()
            continue

        amount = min(_money(payment.balance), remaining)
        allocation = _apply_payment_to_invoice(payment, invoice, amount)
        if allocation:
            allocations.append(allocation)

        if _money(payment.balance) <= 0:
            break

    return allocations


@transaction.atomic
def allocate_credit_to_rent_invoice(invoice):
    """
    Apply existing tenant credit to a newly-created/open rent invoice.
    """
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.type != RENT_TYPE or _money(invoice.get_remaining_balance()) <= 0:
        return []

    allocations = []
    payments = Payment.objects.select_for_update().filter(
        user=invoice.user,
        tenant=invoice.tenant,
        balance__gt=0,
    ).order_by('date', 'id')

    for payment in payments:
        remaining = _money(invoice.get_remaining_balance())
        if remaining <= 0:
            invoice.update_status()
            break

        amount = min(_money(payment.balance), remaining)
        allocation = _apply_payment_to_invoice(payment, invoice, amount)
        if allocation:
            allocations.append(allocation)

    return allocations


def get_rent_balance_summary(user, tenant=None, through_date=None):
    invoices = Invoice.objects.filter(user=user, type=RENT_TYPE)
    credits = Payment.objects.filter(user=user, balance__gt=0)

    if tenant:
        invoices = invoices.filter(tenant=tenant)
        credits = credits.filter(tenant=tenant)

    if through_date:
        invoices = invoices.filter(due_date__lte=through_date)

    arrears_total = sum(_money(invoice.get_remaining_balance()) for invoice in invoices)
    credit_total = sum(_money(payment.balance) for payment in credits)
    return {
        'arrears_total': arrears_total,
        'credit_total': credit_total,
        'net_balance': arrears_total - credit_total,
    }
