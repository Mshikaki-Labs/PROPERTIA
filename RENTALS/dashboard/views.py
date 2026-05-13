from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views import View
from properties.models import Property
from tenants.models import Tenant
from payments.models import Payment
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@login_required
def index(request):
    # Get counts and statistics
    total_properties = Property.objects.filter(user=request.user).count()
    total_tenants = Tenant.objects.filter(user=request.user).count()
    total_units = Property.objects.filter(user=request.user).aggregate(total_units=Sum('total_units'))['total_units'] or 0
    maintenance_requests = 0  # No maintenance model created yet
    
    # Get recent properties (last 5) and annotate with occupancy
    recent_properties_qs = Property.objects.filter(user=request.user)[:5]
    recent_properties = []
    for prop in recent_properties_qs:
        occupied_units = prop.units.filter(user=request.user, status='occupied').count() if hasattr(prop, 'units') else 0
        total_units = prop.units.filter(user=request.user).count() if hasattr(prop, 'units') else prop.total_units
        recent_properties.append({
            'id': prop.id,
            'name': prop.name,
            'address': prop.address,
            'county': prop.county,
            'total_units': total_units,
            'occupied_units': occupied_units,
            'description': prop.description,
            'property_image': prop.property_image.url if prop.property_image else '',
        })
    
    # Get recent tenants (last 4)
    recent_tenants = Tenant.objects.filter(user=request.user)[:4]
    
    # Calculate monthly revenue (payments from last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_revenue = Payment.objects.filter(
        user=request.user,
        date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate percentage changes
    previous_month = timezone.now() - timedelta(days=60)
    prev_month_revenue = Payment.objects.filter(
        user=request.user,
        date__gte=previous_month,
        date__lt=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_increase = 0
    if prev_month_revenue > 0:
        revenue_increase = ((monthly_revenue - prev_month_revenue) / prev_month_revenue) * 100
    
    context = {
        'total_properties': total_properties,
        'total_tenants': total_tenants,
        'total_units': total_units,
        'maintenance_requests': maintenance_requests,
        'monthly_revenue': monthly_revenue,
        'revenue_increase': round(revenue_increase, 1),
        'recent_properties': recent_properties,
        'recent_tenants': recent_tenants,
        'user_initial': request.user.first_name[0] + request.user.last_name[0] if request.user.is_authenticated and request.user.first_name and request.user.last_name else 'U',
        'user_name': f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated and request.user.first_name else 'User'
    }
    
    return render(request, 'dashboard/dashboard.html', context)