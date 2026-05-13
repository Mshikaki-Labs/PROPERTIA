from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from properties.models import Property
from tenants.models import Tenant

class Payment(models.Model):
    STATUS_CHOICES = [
        ('claimed', 'Claimed'),
        ('unclaimed', 'Unclaimed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payments')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Remaining unallocated amount
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unclaimed')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Set balance to amount on first creation
        if not self.pk and self.balance == 0:
            self.balance = self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant.first_name} {self.tenant.last_name} - {self.amount}"