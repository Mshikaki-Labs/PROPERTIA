from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse


from .models import WaterBill
from units.models import Unit

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
        return redirect('water_bills:list')

    return render(request, 'water_bills/water_bills_view.html', {
        'bills': WaterBill.objects.filter(user=request.user).order_by('-due_date'),
        'units': Unit.objects.filter(user=request.user, status='occupied')
    })