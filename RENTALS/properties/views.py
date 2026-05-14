from django.shortcuts import render, redirect, get_object_or_404
from .models import Property
from .forms import PropertyForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
def property_list(request):
    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.user = request.user
            property_obj.save()
            return redirect('properties:properties_home')
    
    properties = Property.objects.filter(user=request.user)
    form = PropertyForm()
    return render(request, 'properties/propertyIndex.html', {
        'properties': properties,
        'form': form
    })

@login_required
def edit_property(request, pk):
    """Edit a property"""
    property_obj = get_object_or_404(Property, pk=pk, user=request.user)
    
    if request.method == "POST":
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Property updated successfully'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        return JsonResponse({
            'id': property_obj.id,
            'name': property_obj.name,
            'address': property_obj.address,
            'county': property_obj.county,
            'total_units': property_obj.total_units,
            'description': property_obj.description
        })
    
    # Return form for regular requests
    form = PropertyForm(instance=property_obj)
    return render(request, 'properties/propertyIndex.html', {'form': form, 'edit_property': property_obj})


@require_POST
def delete_properties(request):
    """Delete selected properties"""
    property_ids = request.POST.getlist('property_ids[]')
    
    if property_ids:
        Property.objects.filter(id__in=property_ids).delete()
        return JsonResponse({'success': True, 'message': f'{len(property_ids)} property/ies deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'No properties selected'})

