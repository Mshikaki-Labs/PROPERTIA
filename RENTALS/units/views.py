from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Prefetch
import csv
import json

# Create your views here.


from .models import Unit
from tenants.models import Tenant
from properties.models import Property
from django import forms
from django.contrib.auth.decorators import login_required

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['property', 'name', 'rent_amount', 'description']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. House 712'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

@login_required
def units_list(request):
    # 1. Handle POST (Form Submission)
    if request.method == "POST":
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.user = request.user
            unit.save()
            return redirect('units:units_list')
        # If form is NOT valid, we don't reset it; we let it pass 
        # to the template so the user can see the error messages.
    else:
        # 2. Handle GET (Initial Page Load)
        form = UnitForm()

    # 3. Filtering Logic (Common to both or just GET)
    units = Unit.objects.filter(user=request.user).select_related('property').prefetch_related(
        Prefetch('tenants', queryset=Tenant.objects.order_by('last_name'), to_attr='prefetched_tenants')
    )
    property_filter = request.GET.get('property')
    status_filter = request.GET.get('status')
    
    if property_filter:
        units = units.filter(property_id=property_filter)
    if status_filter:
        units = units.filter(status=status_filter)
            
    today_date = timezone.now().date()
    # 4. Return the Response
    return render(request, 'units/units_view.html', {
        'units': units,
        'form': form, # This is now guaranteed to exist!
        'properties': Property.objects.filter(user=request.user),
        'tenants': Tenant.objects.filter(user=request.user, unit__isnull=True),
        'today_date': today_date,
    })


def assign_tenant(request, pk):
    """Assign a tenant to a unit"""
    unit = get_object_or_404(Unit, pk=pk)

    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        start_date = request.POST.get('start_date')
        deposit_held = request.POST.get('deposit_held', 0)
        if tenant_id:
            try:
                from leases.models import Lease
                tenant = Tenant.objects.filter(id=tenant_id, user=request.user).exclude(leases__is_active=True).first()
                if not tenant:
                    return JsonResponse({'success': False, 'message': 'Selected tenant is not available or does not belong to you.'}, status=400)
                if tenant.leases.filter(is_active=True).exists():
                    return JsonResponse({'success': False, 'message': 'Tenant already has an active lease.'}, status=400)
                # Check for existing active lease on unit
                if Lease.objects.filter(unit=unit, is_active=True).exists():
                    return JsonResponse({'success': False, 'message': f'Unit {unit.name} already has an active lease.'}, status=400)
                # Create lease
                lease = Lease.objects.create(
                    user=request.user,
                    tenant=tenant,
                    unit=unit,
                    start_date=start_date or timezone.now().date(),
                    monthly_rent=unit.rent_amount,
                    deposit_held=deposit_held,
                    is_active=True
                )
                tenant.unit = unit
                tenant.property = unit.property
                tenant.save()
                # Lease creation will handle unit status and tenant activation
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f'Lease created: {tenant.first_name} {tenant.last_name} assigned to {unit.name}'})
                else:
                    return redirect('units:units_list')
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
        else:
            return JsonResponse({'success': False, 'message': 'Please select a tenant'}, status=400)

    # Return available tenants for modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        tenants = Tenant.objects.filter(property=unit.property, user=request.user, unit__isnull=True).exclude(leases__is_active=True).order_by('last_name')
        return JsonResponse({
            'unit_id': unit.id,
            'unit_name': unit.name,
            'tenants': list(tenants.values('id', 'first_name', 'last_name')),
            'message': f'{tenants.count()} tenant(s) available for {unit.name}'
        })


def detach_tenant(request, pk):
    """Detach tenant from a unit"""
    unit = get_object_or_404(Unit, pk=pk)
    
    if request.method == 'POST':
        from leases.models import Lease
        # Find and deactivate the active lease for this unit
        lease = Lease.objects.filter(unit=unit, is_active=True).first()
        if lease:
            lease.is_active = False
            lease.save()
            # Optionally set tenant.unit = None if needed
            if hasattr(lease.tenant, 'unit'):
                lease.tenant.unit = None
                lease.tenant.save()
        
        return JsonResponse({'success': True, 'message': f'Tenant detached from {unit.name}'})


@require_POST
def delete_units(request):
    """Delete selected units"""
    unit_ids = request.POST.getlist('unit_ids[]')
    
    if unit_ids:
        Unit.objects.filter(id__in=unit_ids).delete()
        return JsonResponse({'success': True, 'message': f'{len(unit_ids)} unit/s deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'No units selected'})


@require_POST
def upload_units(request):
    """Upload units from CSV or XLSX file"""
    def parse_decimal(value):
        if value is None or str(value).strip() == '':
            raise ValueError('Missing rent_amount')
        return float(str(value).replace(',', '').strip())

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'message': 'No file provided'})
    
    file = request.FILES['file']
    filename = file.name.lower()
    
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
        
        for idx, row in enumerate(rows, start=2):
            try:
                row_lower = {k.lower().strip(): v for k, v in row.items()}
                
                property_name = row_lower.get('property')
                unit_name = row_lower.get('name')
                rent_amount = row_lower.get('rent_amount')
                
                if not property_name or not unit_name or rent_amount is None or str(rent_amount).strip() == '':
                    errors.append(f'Row {idx}: Missing required fields (property, name, rent_amount)')
                    continue
                
                property_obj = Property.objects.filter(name__iexact=property_name, user=request.user).first()
                if not property_obj:
                    errors.append(f'Row {idx}: Property "{property_name}" not found for this user')
                    continue
                
                try:
                    rent_amount_val = parse_decimal(rent_amount)
                except ValueError as ve:
                    errors.append(f'Row {idx}: Invalid rent_amount "{rent_amount}"')
                    continue
                
                unit_data = {
                    'user': request.user,
                    'property': property_obj,
                    'name': unit_name,
                    'rent_amount': rent_amount_val,
                    'description': row_lower.get('description', ''),
                    'status': row_lower.get('status', 'vacant').lower(),
                }
                
                Unit.objects.create(**unit_data)
                created_count += 1
                
            except ValueError as ve:
                errors.append(f'Row {idx}: Invalid data format - {str(ve)}')
            except Exception as e:
                errors.append(f'Row {idx}: {str(e)}')
        
        message = f'Successfully created {created_count} units'
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