from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from properties.models import Property
from units.models import Unit
from PROPATIA.pagination import paginate_queryset

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse

@login_required
def index(request):
    maintenance_list = []
    pagination = paginate_queryset(request, maintenance_list)
    context = {
        'maintenance_list': pagination['page_obj'],
        'properties': Property.objects.filter(user=request.user),
        'units': Unit.objects.filter(user=request.user),
        'selected_property': request.GET.get('property', ''),
        'selected_status': request.GET.get('status', ''),
    }
    context.update(pagination)
    return render(request, 'maintenance/maintenance_view.html', context)
