from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone

from properties.models import Property
from units.models import Unit
from tenants.models import Tenant
from invoices.models import Invoice
from payments.models import Payment
from .models import Arrears
from PROPATIA.pagination import paginate_queryset


def sync_user_arrears(user):
    """Keep arrears records aligned with currently overdue invoices."""
    today = timezone.now().date()
    overdue_invoices = Invoice.objects.filter(
        user=user,
        due_date__lt=today,
        status__in=['Unpaid', 'Partially Paid'],
    ).select_related('tenant', 'unit', 'user')

    active_invoice_ids = []
    for invoice in overdue_invoices:
        remaining_balance = invoice.get_remaining_balance()
        if remaining_balance <= 0:
            continue

        active_invoice_ids.append(invoice.id)
        days_overdue = (today - invoice.due_date).days
        arrears_record, _created = Arrears.objects.get_or_create(
            invoice=invoice,
            tenant=invoice.tenant,
            defaults={
                'tenant': invoice.tenant,
                'unit': invoice.unit,
                'user': invoice.user,
                'amount_due': remaining_balance,
                'days_overdue': days_overdue,
                'status': 'pending',
            }
        )

        arrears_record.user = invoice.user
        arrears_record.tenant = invoice.tenant
        arrears_record.unit = invoice.unit
        arrears_record.amount_due = remaining_balance
        arrears_record.days_overdue = days_overdue
        if arrears_record.status == 'resolved':
            arrears_record.status = 'pending'
            arrears_record.date_resolved = None
        arrears_record.save()

    resolved_records = Arrears.objects.filter(
        user=user,
        status='pending',
    ).exclude(invoice_id__in=active_invoice_ids)
    for arrears_record in resolved_records:
        arrears_record.mark_resolved()


@login_required
def arrears_report(request):
    sync_user_arrears(request.user)

    # 1. Get filter parameters
    prop_id = request.GET.get('property')
    unit_id = request.GET.get('unit')
    tenant_id = request.GET.get('tenant')
    status_filter = request.GET.get('status', 'all')

    # 2. Base Query: Start with Arrears records
    arrears_records = Arrears.objects.filter(user=request.user).select_related(
        'invoice', 'tenant', 'unit', 'unit__property'
    ).order_by('-date_marked')

    # 3. Apply Filters
    if prop_id:
        arrears_records = arrears_records.filter(unit__property_id=prop_id)
    if unit_id:
        arrears_records = arrears_records.filter(unit_id=unit_id)
    if tenant_id:
        arrears_records = arrears_records.filter(tenant_id=tenant_id)
    
    # Filter by status (default to pending)
    if status_filter and status_filter != 'all':
        arrears_records = arrears_records.filter(status=status_filter)

    total_arrears_amount = arrears_records.aggregate(total=Sum('amount_due'))['total'] or 0
    total_records = arrears_records.count()
    pagination = paginate_queryset(request, arrears_records)

    # 5. Get available filter options
    properties = Property.objects.filter(user=request.user)
    units = Unit.objects.filter(user=request.user).select_related('property').order_by('property__name', 'name')
    if prop_id:
        units = units.filter(property_id=prop_id)
    tenants = Tenant.objects.filter(user=request.user, status='active').order_by('first_name', 'last_name')
    if prop_id:
        tenants = tenants.filter(unit__property_id=prop_id)

    # 6. Context
    context = {
        'report_data': pagination['page_obj'],
        'total_arrears_amount': total_arrears_amount,
        'total_records': total_records,
        'properties': properties,
        'units': units,
        'tenants': tenants,
        'selected_property': prop_id,
        'selected_unit': unit_id,
        'selected_tenant': tenant_id,
        'selected_status': status_filter,
        'title': 'Arrears Report'
    }
    context.update(pagination)

    return render(request, 'arrears/arrears_report.html', context)
