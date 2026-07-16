from django import forms
from .models import Tenant
from properties.models import Property

class TenantForm(forms.ModelForm):
    # Add a property field that's not in the model
    property = forms.ModelChoiceField(
        queryset=Property.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Property',
        required=True
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        queryset = Property.objects.none()
        if user is not None and user.is_authenticated:
            queryset = Property.objects.filter(user=user).order_by('name')
        self.fields['property'].queryset = queryset
        if self.instance and self.instance.pk and self.instance.unit_id:
            self.fields['property'].initial = self.instance.unit.property_id

    class Meta:
        model = Tenant
        fields = ['first_name', 'last_name', 'phone_number', 'next_of_kin_name', 'description', 'deposit_required', 'deposit_amount', 'next_of_kin_phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'next_of_kin_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deposit_required': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'depositCheck'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter deposit amount'}),
            'next_of_kin_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
