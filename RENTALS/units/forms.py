from django import forms
from properties.models import Property
from .models import Unit

class UnitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        queryset = Property.objects.all()
        if user is not None:
            queryset = queryset.filter(user=user)
        self.fields['property'].queryset = queryset

    class Meta:
        model = Unit
        fields = ['property', 'name', 'rent_amount', 'description']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }