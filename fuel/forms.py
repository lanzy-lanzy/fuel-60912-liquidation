from django import forms
from .models import FuelConsumption

class FuelConsumptionForm(forms.ModelForm):
    class Meta:
        model = FuelConsumption
        fields = ['driver', 'date', 'number_of_trips', 'purpose']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'number_of_trips': forms.NumberInput(attrs={'min': 1}),
            'purpose': forms.TextInput(attrs={'placeholder': 'Enter trip purpose'})
        }