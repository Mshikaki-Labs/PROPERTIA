from django.http import JsonResponse
from django.shortcuts import render
from .models import Lease
from properties.models import Property
from units.models import Unit
from django.contrib.auth.decorators import login_required
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties

@login_required
def index(request):
    accessible_props = get_accessible_properties(request.user)

    leases = Lease.objects.filter(
        unit__property__in=accessible_props,
        is_active=True
    ).select_related('tenant', 'unit', 'unit__property').order_by('unit__property__name', 'unit__name')
    
    selected_property = request.GET.get('property', '')
    selected_unit = request.GET.get('unit', '')

    properties = accessible_props.order_by('name')
    allowed_property_ids = set(properties.values_list('id', flat=True))

    if selected_property and selected_property.isdigit() and int(selected_property) in allowed_property_ids:
        leases = leases.filter(unit__property_id=selected_property)
    else:
        selected_property = ''

    units = Unit.objects.filter(property__in=accessible_props).select_related('property').order_by('property__name', 'name')
    if selected_property:
        units = units.filter(property_id=selected_property)

    allowed_unit_ids = set(units.values_list('id', flat=True))
    if selected_unit and selected_unit.isdigit() and int(selected_unit) in allowed_unit_ids:
        leases = leases.filter(unit_id=selected_unit)
    else:
        selected_unit = ''

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


@login_required
def units_for_property(request):
    accessible_props = get_accessible_properties(request.user)
    property_id = request.GET.get('property', '')
    units = Unit.objects.filter(property__in=accessible_props).select_related('property').order_by('property__name', 'name')

    if property_id:
        if not property_id.isdigit() or not accessible_props.filter(id=property_id).exists():
            return JsonResponse({'units': []})
        units = units.filter(property_id=property_id)

    unit_options = [
        {
            'id': unit.id,
            'name': unit.name,
            'property': unit.property.name,
        }
        for unit in units
    ]
    return JsonResponse({'units': unit_options})
