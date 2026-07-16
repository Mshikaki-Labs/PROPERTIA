from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from properties.models import Property
from units.models import Unit
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties

@login_required
def index(request):
    accessible_props = get_accessible_properties(request.user)
    maintenance_list = []
    pagination = paginate_queryset(request, maintenance_list)
    context = {
        'maintenance_list': pagination['page_obj'],
        'properties': accessible_props.order_by('name'),
        'units': Unit.objects.filter(property__in=accessible_props).order_by('name'),
        'selected_property': request.GET.get('property', ''),
        'selected_status': request.GET.get('status', ''),
    }
    context.update(pagination)
    return render(request, 'maintenance/maintenance_view.html', context)
