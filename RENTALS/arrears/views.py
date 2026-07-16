from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from collections import OrderedDict

from properties.models import Property
from units.models import Unit
from tenants.models import Tenant
from invoices.models import Invoice
from payments.models import Payment
from .models import Arrears
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties


def sync_user_arrears(user):
    """Keep arrears records aligned with currently overdue invoices."""
    today = timezone.now().date()
    accessible_props = get_accessible_properties(user)
    overdue_invoices = Invoice.objects.filter(
        unit__property__in=accessible_props,
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
    accessible_props = get_accessible_properties(request.user)

    # 1. Get filter parameters
    prop_id = request.GET.get('property')
    unit_id = request.GET.get('unit')
    tenant_id = request.GET.get('tenant')
    status_filter = request.GET.get('status', 'all')

    # 2. Base Query: Start with Arrears records (scoped to accessible properties)
    arrears_records = Arrears.objects.filter(
        unit__property__in=accessible_props
    ).select_related(
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

    monthly_groups = OrderedDict()
    tenant_running_totals = {}
    monthly_source = arrears_records.order_by('tenant__last_name', 'tenant__first_name', 'invoice__due_date', 'id')
    for record in monthly_source:
        month_key = record.invoice.due_date.replace(day=1)
        key = (record.tenant_id, record.unit_id, month_key)
        if key not in monthly_groups:
            monthly_groups[key] = {
                'tenant': record.tenant,
                'unit': record.unit,
                'month': month_key,
                'monthly_arrears': 0,
                'accumulated_arrears': 0,
            }
        monthly_groups[key]['monthly_arrears'] += record.amount_due

    monthly_arrears = []
    for group in monthly_groups.values():
        tenant_id = group['tenant'].id
        tenant_running_totals[tenant_id] = tenant_running_totals.get(tenant_id, 0) + group['monthly_arrears']
        group['accumulated_arrears'] = tenant_running_totals[tenant_id]
        monthly_arrears.append(group)

    pagination = paginate_queryset(request, arrears_records)

    # 5. Get available filter options (scoped to accessible properties)
    properties = accessible_props
    units = Unit.objects.filter(property__in=accessible_props).select_related('property').order_by('property__name', 'name')
    if prop_id:
        units = units.filter(property_id=prop_id)
    tenants = Tenant.objects.filter(unit__property__in=accessible_props, status='active').order_by('first_name', 'last_name')
    if prop_id:
        tenants = tenants.filter(unit__property_id=prop_id)

    # 6. Context
    context = {
        'report_data': pagination['page_obj'],
        'page_obj': pagination['page_obj'],
        'total_arrears_amount': total_arrears_amount,
        'total_records': total_records,
        'monthly_arrears': monthly_arrears,
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
