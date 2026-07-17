from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from properties.models import Property
from units.models import Unit
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties
from .models import Maintenance
from .forms import MaintenanceForm


@login_required
def index(request):
    accessible_props = get_accessible_properties(request.user)
    maintenance_list = Maintenance.objects.filter(property__in=accessible_props).select_related('property', 'unit').order_by('-date')
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


@login_required
def create_maintenance(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, user=request.user)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.user = request.user
            maintenance.save()
            return JsonResponse({'success': True, 'message': 'Maintenance record added successfully'})
        return JsonResponse({'success': False, 'message': 'Invalid data', 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
