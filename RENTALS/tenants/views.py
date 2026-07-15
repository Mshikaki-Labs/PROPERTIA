from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import Tenant
from .forms import TenantForm
from invoices.models import Invoice
from payments.models import Payment
from properties.models import Property
from units.models import Unit
from PROPATIA.pagination import paginate_queryset


@login_required
def tenant_list(request):
    if request.method == "POST":
        form = TenantForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('tenants:tenant_list')
    else:
        form = TenantForm(user=request.user)

    Tenant.objects.filter(Q(unit__isnull=True) | Q(unit__property__isnull=True)).delete()

    user_properties = Property.objects.filter(user=request.user)
    tenants = Tenant.objects.filter(unit__property__user=request.user).select_related('unit', 'unit__property').order_by('last_name', 'first_name')

    property_filter = request.GET.get('property')
    status_filter = request.GET.get('status')
    allowed_property_ids = set(user_properties.values_list('id', flat=True))

    if property_filter and property_filter.isdigit() and int(property_filter) in allowed_property_ids:
        tenants = tenants.filter(unit__property_id=property_filter)
    else:
        property_filter = None

    if status_filter:
        tenants = tenants.filter(status=status_filter)

    pagination = paginate_queryset(request, tenants)

    return render(request, 'tenants/tenants_view.html', {
        'tenants': pagination['page_obj'],
        'form': form,
        'properties': user_properties,
        'selected_property': property_filter,
        'selected_status': status_filter,
        **pagination,
    })


@login_required
def available_units(request, pk):
    """Return units for a property as JSON."""
    property_obj = get_object_or_404(Property, pk=pk, user=request.user)
    units = Unit.objects.filter(property=property_obj, user=request.user).values('id', 'name', 'rent_amount')
    return JsonResponse({'property': property_obj.name, 'units': list(units)})


@login_required
def tenant_ledger(request, pk):
    """Render the tenant ledger with invoices and payments for the tenant/unit."""
    tenant = get_object_or_404(
        Tenant.objects.select_related('unit', 'unit__property'),
        pk=pk,
        unit__property__user=request.user,
    )

    invoices = Invoice.objects.filter(tenant=tenant).select_related('unit').order_by('due_date', 'id')
    payments = Payment.objects.filter(tenant=tenant).select_related('unit').order_by('date', 'id')

    ledger_entries = []
    for invoice in invoices:
        ledger_entries.append({
            'date': invoice.due_date,
            'code': '',
            'description': f"Invoice {invoice.invoice_number}",
            'debit': invoice.amount,
            'credit': 0,
            'status': invoice.status,
            'is_overdue': invoice.due_date < date.today() and invoice.status != 'Paid',
            'type': 'invoice',
        })

    for payment in payments:
        ledger_entries.append({
            'date': payment.date,
            'code': payment.code or '',
            'description': payment.description or 'Payment received',
            'debit': 0,
            'credit': payment.amount,
            'status': payment.status,
            'is_overdue': False,
            'type': 'payment',
        })

    ledger_entries.sort(key=lambda item: (item['date'], item['type'] != 'invoice'))

    running_balance = 0
    for entry in ledger_entries:
        running_balance += entry['debit'] - entry['credit']
        entry['balance'] = running_balance

    total_invoiced = sum(invoice.amount for invoice in invoices)
    total_paid = sum(payment.amount for payment in payments)
    current_balance = total_invoiced - total_paid
    overdue_count = sum(
        1 for invoice in invoices if invoice.due_date < date.today() and invoice.status != 'Paid'
    )

    return render(request, 'tenants/tenant_ledger.html', {
        'tenant': tenant,
        'ledger_entries': ledger_entries,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'current_balance': current_balance,
        'overdue_count': overdue_count,
    })


@login_required
def delete_tenants(request):
    """Delete selected tenants."""
    if request.method == 'POST':
        tenant_ids = request.POST.getlist('tenant_ids[]')
        deleted_count, _ = Tenant.objects.filter(
            id__in=tenant_ids,
            unit__property__user=request.user,
        ).delete()
        return JsonResponse({'success': True, 'message': f'{deleted_count} tenant(s) deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def edit_tenant(request, pk):
    """Edit an existing tenant."""
    tenant = get_object_or_404(
        Tenant.objects.select_related('unit', 'unit__property'),
        pk=pk,
        unit__property__user=request.user,
    )
    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES, instance=tenant, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('tenants:tenant_list')
    else:
        form = TenantForm(instance=tenant, user=request.user)

    return render(request, 'tenants/edit_tenant.html', {'form': form, 'tenant': tenant})


@login_required
def upload_tenants(request):
    """Accept tenant uploads and return a JSON response."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'success': False, 'message': 'No file uploaded'})

    return JsonResponse({'success': True, 'message': 'Upload received'})
