from django.shortcuts import render
from .models import Lease
from properties.models import Property
from units.models import Unit
from django.contrib.auth.decorators import login_required
from PROPATIA.pagination import paginate_queryset

@login_required
def index(request):
    leases = Lease.objects.filter(user=request.user, is_active=True).select_related('tenant', 'unit', 'unit__property').order_by('unit__property__name', 'unit__name')
    
    selected_property = request.GET.get('property')
    selected_unit = request.GET.get('unit')
    
    if selected_property:
        leases = leases.filter(unit__property_id=selected_property)
    if selected_unit:
        leases = leases.filter(unit_id=selected_unit)
    
    properties = Property.objects.filter(user=request.user)
    units = Unit.objects.filter(user=request.user)

    pagination = paginate_queryset(request, leases)
    
    context = {
        'leases': pagination['page_obj'],
        'properties': properties,
        'units': units,
        'selected_property': selected_property,
        'selected_unit': selected_unit,
    }
    context.update(pagination)
    return render(request, 'leases/leases_view.html', context)
