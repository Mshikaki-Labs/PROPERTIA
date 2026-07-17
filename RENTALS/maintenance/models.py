from django.db import models
from django.contrib.auth.models import User
from properties.models import Property
from units.models import Unit


class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_records')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True, related_name='maintenance_records')
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Maintenance: {self.property.name} - {self.description}"
