from django import forms
from .models import Tenant
from properties.models import Property

class TenantForm(forms.ModelForm):
    property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Property',
        required=True
    )

    class Meta:
        model = Tenant
        fields = ['first_name', 'last_name', 'phone_number', 'property', 'id_card_front', 'id_card_back', 'kra_pin', 'next_of_kin_name', 'next_of_kin_phone_number', 'description', 'status', 'deposit_required', 'deposit_amount']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'id_card_front': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_back': forms.FileInput(attrs={'class': 'form-control'}),
            'kra_pin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter KRA PIN'}),
            'next_of_kin_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter next of kin name'}),
            'next_of_kin_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter next of kin phone'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'deposit_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter deposit amount'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
        self.fields['id_card_front'].required = False
        self.fields['id_card_back'].required = False
        self.fields['kra_pin'].required = False
        if user:
            self.fields['property'].queryset = Property.objects.filter(user=user)
