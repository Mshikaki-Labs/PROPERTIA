from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from units.models import Unit
from tenants.models import Tenant

class WaterBill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    previous_reading = models.IntegerField()
    current_reading = models.IntegerField()
    consumption = models.IntegerField(editable=False)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    due_date = models.DateField()
    status = models.CharField(max_length=10, default='Unpaid')

    def save(self, *args, **kwargs):
        self.consumption = self.current_reading - self.previous_reading
        self.amount = self.consumption * self.rate
        super().save(*args, **kwargs)