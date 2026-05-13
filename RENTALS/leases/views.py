from django.shortcuts import render
from .models import Lease
from properties.models import Property
from units.models import Unit
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    leases = Lease.objects.filter(user=request.user, is_active=True).select_related('tenant', 'unit', 'unit__property')
    
    selected_property = request.GET.get('property')
    selected_unit = request.GET.get('unit')
    
    if selected_property:
        leases = leases.filter(unit__property_id=selected_property)
    if selected_unit:
        leases = leases.filter(unit_id=selected_unit)
    
    properties = Property.objects.filter(user=request.user)
    units = Unit.objects.filter(user=request.user)
    
    return render(request, 'leases/leases_view.html', {
        'leases': leases,
        'properties': properties,
        'units': units,
        'selected_property': selected_property,
        'selected_unit': selected_unit,
    })
