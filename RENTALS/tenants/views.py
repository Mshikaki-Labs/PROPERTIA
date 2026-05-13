from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q, Sum

from django.views.decorators.http import require_POST
from .models import Tenant
from .forms import TenantForm
from django.http import JsonResponse
from properties.models import Property
from units.models import Unit
import csv
from django.contrib.auth.decorators import login_required

@login_required
def tenant_list(request):
    if request.method == "POST":
        form = TenantForm(request.POST, user=request.user)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.user = request.user
            tenant.save()
            return redirect('tenants:tenant_list')
    else:
        form = TenantForm(user=request.user)

    # Filtering
    tenants = Tenant.objects.filter(user=request.user)
    property_filter = request.GET.get('property')
    status_filter = request.GET.get('status')

    if property_filter:
        # Filter by property: show tenants in that property either by explicit tenant.property or by assigned unit property
        tenants = tenants.filter(Q(property_id=property_filter) | Q(unit__property_id=property_filter))
    
    if status_filter:
        tenants = tenants.filter(status=status_filter)

    tenants = tenants.select_related('property', 'unit').order_by('last_name', 'first_name')

    return render(request, 'tenants/tenants_view.html', {
        'tenants': tenants,
        'form': form,
        'properties': Property.objects.filter(user=request.user),
        'selected_property': property_filter,
        'selected_status': status_filter,
    })

@login_required
def edit_tenant(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk, user=request.user)
    
    if request.method == "POST":
        form = TenantForm(request.POST, instance=tenant, user=request.user)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.user = request.user
            tenant.save()
            return redirect('tenants:tenant_list')
    else:
        form = TenantForm(instance=tenant, user=request.user)
    
    return render(request, 'tenants/edit_tenant.html', {
        'form': form,
        'tenant': tenant,
        'properties': Property.objects.filter(user=request.user),
    })

@login_required
def available_units(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk, user=request.user)
    unit_query = Unit.objects.filter(user=request.user).exclude(leases__is_active=True)
    if tenant.property:
        unit_query = unit_query.filter(property=tenant.property)
    else:
        unit_query = unit_query.filter(status='vacant')

    units = unit_query.select_related('property').order_by('name').values('id', 'name', 'property__name')
    return JsonResponse({
        'tenant_id': tenant.id,
        'tenant_name': f'{tenant.first_name} {tenant.last_name}',
        'units': list(units)
    })


@login_required
def tenant_ledger(request, pk):
    """
    Display the ledger for a specific tenant showing all invoices, payments,
    and running balance.
    """
    from invoices.models import Invoice, InvoicePayment
    from payments.models import Payment
    from django.utils import timezone
    
    tenant = get_object_or_404(Tenant, pk=pk, user=request.user)
    
    # Get all invoices for this tenant
    invoices = Invoice.objects.filter(
        user=request.user, 
        tenant=tenant
    ).select_related('unit').order_by('due_date')
    
    # Get all payments for this tenant
    payments = Payment.objects.filter(
        user=request.user, 
        tenant=tenant
    ).order_by('date')
    
    # Build ledger entries (combined invoices and payments with running balance)
    ledger_entries = []
    running_balance = 0
    
    # Add invoices to ledger
    for invoice in invoices:
        running_balance += invoice.amount
        ledger_entries.append({
            'type': 'invoice',
            'date': invoice.due_date,
            'description': f'Invoice {invoice.invoice_number} ({invoice.get_type_display()})',
            'debit': invoice.amount,
            'credit': None,
            'balance': running_balance,
            'status': invoice.status,
            'invoice_id': invoice.id,
            'is_overdue': invoice.due_date < timezone.now().date() and invoice.status != 'Paid',
        })
    
    # Add payments to ledger
    for payment in payments:
        running_balance -= payment.amount
        ledger_entries.append({
            'type': 'payment',
            'date': payment.date,
            'description': f'Payment ({payment.description or "No description"}) - {payment.status}',
            'debit': None,
            'credit': payment.amount,
            'balance': running_balance,
            'status': payment.status,
            'payment_id': payment.id,
            'is_overdue': False,
        })
    
    # Sort by date
    ledger_entries.sort(key=lambda x: x['date'])
    
    # Recalculate running balance after sorting
    recalculated_balance = 0
    for entry in ledger_entries:
        if entry['type'] == 'invoice':
            recalculated_balance += entry['debit']
        else:
            recalculated_balance -= entry['credit']
        entry['balance'] = recalculated_balance
    
    # Summary statistics
    total_invoiced = invoices.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    current_balance = total_invoiced - total_paid
    
    # Count overdue invoices
    overdue_count = invoices.filter(
        due_date__lt=timezone.now().date(),
        status__in=['Unpaid', 'Partially Paid']
    ).count()
    
    context = {
        'tenant': tenant,
        'ledger_entries': ledger_entries,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'current_balance': current_balance,
        'overdue_count': overdue_count,
        'title': f'Tenant Ledger - {tenant.first_name} {tenant.last_name}',
    }
    
    return render(request, 'tenants/tenant_ledger.html', context)

@require_POST
def delete_tenants(request):
    # getlist gets all values sent under 'tenant_ids[]'
    tenant_ids = request.POST.getlist('tenant_ids[]')
    
    if not tenant_ids:
        return JsonResponse({'success': False, 'message': 'No tenants selected.'})
        
    try:
        # filter and delete
        deleted_count, _ = Tenant.objects.filter(id__in=tenant_ids).delete()
        return JsonResponse({
            'success': True, 
            'message': f'Successfully deleted {deleted_count} tenants.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})



@require_POST
def upload_tenants(request):
    """Upload tenants from CSV or XLSX file. If 'validate_only' POST param is set, only validate and return errors without creating tenants."""
    def parse_decimal(value):
        if value is None or str(value).strip() == '':
            return 0.0
        return float(str(value).replace(',', '').strip())

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'message': 'No file provided'})

    file = request.FILES['file']
    filename = file.name.lower()
    validate_only = request.POST.get('validate_only') == '1'

    try:
        rows = []

        if filename.endswith('.csv'):
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            rows = list(reader)
        elif filename.endswith('.xlsx'):
            try:
                import openpyxl
                from openpyxl import load_workbook
                import io

                wb = load_workbook(io.BytesIO(file.read()))
                ws = wb.active

                headers = [cell.value for cell in ws[1]]

                for row in ws.iter_rows(min_row=2, values_only=False):
                    row_dict = {}
                    for idx, header in enumerate(headers):
                        if header:
                            row_dict[header.lower().strip()] = row[idx].value
                    if any(row_dict.values()):
                        rows.append(row_dict)
            except ImportError:
                return JsonResponse({'success': False, 'message': 'openpyxl is not installed. Please use CSV format or contact admin.'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid file format. Please use CSV or XLSX'})

        if not rows:
            return JsonResponse({'success': False, 'message': 'File is empty'})

        created_count = 0
        errors = []
        valid_rows = 0
        for idx, row in enumerate(rows, start=2):
            try:
                row_lower = {k.lower().strip(): v for k, v in row.items()}

                first_name = row_lower.get('first_name')
                last_name = row_lower.get('last_name')
                phone_number = row_lower.get('phone_number')
                property_name = row_lower.get('property')

                if not first_name or not last_name or not phone_number or not property_name:
                    errors.append(f'Row {idx}: Missing required fields (first_name, last_name, phone_number, property)')
                    continue

                property_obj = Property.objects.filter(name__iexact=property_name, user=request.user).first()
                if not property_obj:
                    errors.append(f'Row {idx}: Property "{property_name}" not found for this user')
                    continue

                deposit_required = True
                if 'deposit_required' in row_lower:
                    deposit_req_val = str(row_lower.get('deposit_required', '')).lower().strip()
                    deposit_required = deposit_req_val in ['true', 'yes', '1', 't', 'y']

                deposit_amount = 0.00
                if row_lower.get('deposit_amount'):
                    try:
                        deposit_amount = parse_decimal(row_lower.get('deposit_amount', 0))
                    except ValueError:
                        errors.append(f'Row {idx}: Invalid deposit_amount "{row_lower.get("deposit_amount")}"')
                        continue

                if not validate_only:
                    tenant_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone_number': phone_number,
                        'property': property_obj,
                        'next_of_kin_name': row_lower.get('next_of_kin_name', ''),
                        'next_of_kin_phone_number': row_lower.get('next_of_kin_phone_number', ''),
                        'description': row_lower.get('description', ''),
                        'status': row_lower.get('status', 'active').lower(),
                        'deposit_required': deposit_required,
                        'deposit_amount': deposit_amount,
                        'user': request.user,
                    }
                    Tenant.objects.create(**tenant_data)
                    created_count += 1
                valid_rows += 1

            except ValueError as ve:
                errors.append(f'Row {idx}: Invalid data format - {str(ve)}')
            except Exception as e:
                errors.append(f'Row {idx}: {str(e)}')

        if validate_only:
            return JsonResponse({
                'success': True,
                'valid_rows': valid_rows,
                'invalid_rows': len(errors),
                'errors': errors,
                'message': f'Validation complete: {valid_rows} valid, {len(errors)} invalid.'
            })

        message = f'Successfully created {created_count} tenants'
        if errors:
            message += f'. {len(errors)} errors: ' + '; '.join(errors[:3])

        response = {
            'success': created_count > 0 or not errors,
            'count': created_count,
            'message': message,
            'errors': errors,
            'invalid_rows': len(errors),
        }
        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error processing file: {str(e)}'})