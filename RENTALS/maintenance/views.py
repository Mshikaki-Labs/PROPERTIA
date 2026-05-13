from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse

@login_required
def index(request):
    return render(request, 'maintenance/maintenance_view.html', {})
