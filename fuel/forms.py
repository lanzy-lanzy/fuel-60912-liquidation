from django import forms
from .models import FuelConsumption
# forms.py
class FuelConsumptionForm(forms.ModelForm):
    class Meta:
        model = FuelConsumption
        fields = ['driver', 'date', 'purpose', 'number_of_trips']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'number_of_trips': forms.NumberInput(attrs={'min': 1}),
            'purpose': forms.TextInput(attrs={'placeholder': 'Enter trip purpose'})
        }