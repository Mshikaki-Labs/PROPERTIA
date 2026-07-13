from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse


from .models import WaterBill
from properties.models import Property
from units.models import Unit
from PROPATIA.pagination import paginate_queryset

@login_required
def water_bill_list(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        prev = int(request.POST.get('previous_reading'))
        curr = int(request.POST.get('current_reading'))
        rate = float(request.POST.get('rate'))
        date = request.POST.get('due_date')
        
        unit = Unit.objects.get(id=unit_id, user=request.user)
        tenant = unit.tenants.filter(status='active').first()
        
        if tenant:
            WaterBill.objects.create(
                user=request.user,
                unit=unit,
                tenant=tenant,
                previous_reading=prev,
                current_reading=curr,
                rate=rate,
                due_date=date
            )
        return redirect('water_bills:water_bills_home')

    selected_property = request.GET.get('property', '')
    selected_unit = request.GET.get('unit', '')
    selected_status = request.GET.get('status', '')
    selected_start_date = request.GET.get('start_date', '')
    selected_end_date = request.GET.get('end_date', '')

    bills = WaterBill.objects.filter(user=request.user).select_related('unit', 'unit__property', 'tenant').order_by('-due_date')

    if selected_property:
        bills = bills.filter(unit__property_id=selected_property)
    if selected_unit:
        bills = bills.filter(unit_id=selected_unit)
    if selected_status:
        bills = bills.filter(status=selected_status)
    if selected_start_date:
        bills = bills.filter(due_date__gte=selected_start_date)
    if selected_end_date:
        bills = bills.filter(due_date__lte=selected_end_date)

    pagination = paginate_queryset(request, bills)

    context = {
        'bills': pagination['page_obj'],
        'properties': Property.objects.filter(user=request.user),
        'units': Unit.objects.filter(user=request.user).select_related('property').order_by('property__name', 'name'),
        'occupied_units': Unit.objects.filter(user=request.user, status='occupied').select_related('property').order_by('property__name', 'name'),
        'selected_property': selected_property,
        'selected_unit': selected_unit,
        'selected_status': selected_status,
        'selected_start_date': selected_start_date,
        'selected_end_date': selected_end_date,
    }
    context.update(pagination)
    return render(request, 'water_bills/water_bills_view.html', context)
