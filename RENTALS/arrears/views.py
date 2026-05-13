from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum

from properties.models import Property
from units.models import Unit
from tenants.models import Tenant
from invoices.models import Invoice
from payments.models import Payment
from .models import Arrears


@login_required
def arrears_report(request):
    # 1. Get filter parameters
    prop_id = request.GET.get('property')
    unit_id = request.GET.get('unit')
    tenant_id = request.GET.get('tenant')
    status_filter = request.GET.get('status', 'pending')

    # 2. Base Query: Start with Arrears records
    arrears_records = Arrears.objects.filter(user=request.user).select_related(
        'invoice', 'tenant', 'unit'
    )

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

    # 4. Calculate Summary Data
    report_data = []
    total_arrears_amount = 0
    
    for arrears in arrears_records:
        report_data.append({
            'arrears': arrears,
            'invoice': arrears.invoice,
            'tenant': arrears.tenant,
            'unit': arrears.unit,
            'amount_due': arrears.amount_due,
            'days_overdue': arrears.days_overdue,
            'status': arrears.status,
            'date_marked': arrears.date_marked,
            'invoice_amount': arrears.invoice.amount,
            'invoice_number': arrears.invoice.invoice_number,
        })
        total_arrears_amount += arrears.amount_due

    # 5. Get available filter options
    properties = Property.objects.filter(user=request.user)
    units = Unit.objects.filter(user=request.user, status='occupied')
    tenants = Tenant.objects.filter(user=request.user, status='active')

    # 6. Context
    context = {
        'report_data': report_data,
        'total_arrears_amount': total_arrears_amount,
        'total_records': len(report_data),
        'properties': properties,
        'units': units,
        'tenants': tenants,
        'selected_property': prop_id,
        'selected_unit': unit_id,
        'selected_tenant': tenant_id,
        'selected_status': status_filter,
        'title': 'Arrears Report'
    }

    return render(request, 'arrears/arrears_report.html', context)
