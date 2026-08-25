from django import forms
from .models import FuelConsumption, Driver, PettyCashVoucher, ReimbursementExpenseReceipt


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'multiple': True, 'accept': 'image/*', 'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class FuelConsumptionForm(forms.ModelForm):
    VEHICLE_CHOICES = [
        ('Ambulance L300', 'Ambulance L300'),
        ('Ambulance Province', 'Ambulance Province'),
        ('Ambulance DOH', 'Ambulance DOH'),
        ('Backhoe', 'Backhoe'),
        ('Dumptruck', 'Dumptruck'),
    ]

    vehicle = forms.ChoiceField(choices=VEHICLE_CHOICES)
    driver = forms.ModelChoiceField(
        queryset=Driver.objects.all(),
        empty_label="Select Driver"
    )
    
    class Meta:
        model = FuelConsumption
        fields = [
            'driver',
            'date',
            'vehicle',
            'destination',
            'trip_number',
            'number_of_trips',
            'purpose',
            'total_liters',
            'cost'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'trip_number': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control'
            }),
            'number_of_trips': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control'
            }),
            'total_liters': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'form-control'
            }),
            'cost': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purpose'].initial = "Transport Patient"
        self.fields['cost'].label = "Cost (₱)"
        self.fields['total_liters'].label = "Fuel Amount (Liters)"
        self.fields['total_liters'].widget.attrs['placeholder'] = 'e.g., 50.00'
        self.fields['cost'].widget.attrs['placeholder'] = 'e.g., 3,000.00'
        self.fields['trip_number'].widget.attrs['placeholder'] = 'e.g., 001'
        self.fields['number_of_trips'].widget.attrs['placeholder'] = 'e.g., 1'
        self.fields['purpose'].widget.attrs['class'] = 'form-control'

        # Ensure every widget gets the styled form-control class
        # (driver / vehicle / destination / purpose render as <select>)
        for field in self.fields.values():
            classes = field.widget.attrs.get('class', '')
            if 'form-control' not in classes:
                field.widget.attrs['class'] = (classes + ' form-control').strip()

        # Set up destination choices based on vehicle type
        # If we have an instance (editing), use its vehicle type
        # Otherwise, default to ambulance destinations
        if self.instance and hasattr(self.instance, 'vehicle'):
            vehicle = self.instance.vehicle
        else:
            # For new forms, we'll update this via JavaScript based on vehicle selection
            vehicle = None
        self._update_destination_choices(vehicle)
        # Note: You should have client-side JavaScript to listen for vehicle field changes
        # and update the destination dropdown accordingly. This is essential for UX.

    def _update_destination_choices(self, vehicle):
        """Update destination choices based on vehicle type"""
        if vehicle in ['Backhoe', 'Dumptruck']:
            # Heavy equipment can only use local area
            self.fields['destination'].choices = FuelConsumption.HEAVY_EQUIPMENT_DESTINATION_CHOICES
            self.fields['destination'].initial = 'local'
        else:
            # Ambulances use all destinations including Mahayag
            # Combine ambulance destinations with Mahayag special choice
            all_ambulance_destinations = (
                FuelConsumption.AMBULANCE_DESTINATION_CHOICES + 
                FuelConsumption.MAHAYAG_SPECIAL_CHOICE
            )
            self.fields['destination'].choices = all_ambulance_destinations

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        destination = cleaned_data.get('destination')
        if vehicle in ['Backhoe', 'Dumptruck'] and destination != 'local':
            self.add_error('destination', "Heavy equipment can only use 'Local Area' as destination.")
        if vehicle in ['Ambulance L300', 'Ambulance Province', 'Ambulance DOH'] and destination == 'local':
            self.add_error('destination', "Ambulances cannot use 'Local Area' as destination.")
        return cleaned_data


class PettyCashVoucherForm(forms.ModelForm):
    class Meta:
        model = PettyCashVoucher
        fields = [
            'voucher_no', 'voucher_date', 'fund', 'fpp',
            'payee_office', 'address',
            'particulars', 'amount', 'purpose',
            'requested_by_name',
            'approved_by_name', 'paid_by_name', 'cash_received_by_name',
            'total_amount_granted', 'total_amount_paid_per_or', 'or_invoice_no',
            'amount_refunded', 'received_refund', 'reimbursement_paid',
            'liquidation_submitted', 'reimbursement_received_by',
        ]
        widgets = {
            'voucher_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'particulars': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'e.g., Office supplies, fuel, etc.'}),
            'purpose': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Purpose of cash advance'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'total_amount_granted': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'total_amount_paid_per_or': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'amount_refunded': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['voucher_no', 'fund', 'fpp', 'payee_office', 'address', 'requested_by_name', 'approved_by_name', 'paid_by_name', 'cash_received_by_name', 'or_invoice_no', 'reimbursement_received_by']:
            if f in self.fields:
                self.fields[f].widget.attrs.update({'class': 'form-control'})
        self.fields['voucher_no'].widget.attrs['placeholder'] = 'e.g., PCV-2026-001'
        self.fields['fund'].widget.attrs['placeholder'] = 'General Fund'
        self.fields['fpp'].widget.attrs['placeholder'] = 'FPP code'


class ReimbursementExpenseReceiptForm(forms.ModelForm):
    # Multi-image upload (handled in view via request.FILES.getlist — also via field clean for validation)
    new_images = MultipleFileField(
        required=False,
        label="Add Images (multiple)",
        help_text="Select one or more JPG/PNG images. They will be laid out in a responsive grid on print and PDF with proper scaling (object-fit contain)."
    )

    class Meta:
        model = ReimbursementExpenseReceipt
        fields = [
            'entity_name', 'fund_cluster', 'receipt_date', 'rer_no',
            'received_from_name', 'received_from_designation',
            'amount_in_words', 'amount_in_figures',
            'in_payment_for',
            'payee_signature_name', 'payee_address', 'payee_residence_cert_no', 'payee_residence_date', 'payee_residence_place',
            'witness_signature_name', 'witness_address', 'witness_residence_cert_no', 'witness_residence_date', 'witness_residence_place',
            'attached_image', 'petty_cash_voucher',
        ]
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payee_residence_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'witness_residence_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'in_payment_for': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Payments for subsistence, services, rental or transportation — include dates, purpose, distance, points of travel, etc.'}),
            'amount_in_words': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., One Thousand Pesos Only'}),
            'amount_in_figures': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['entity_name', 'fund_cluster', 'rer_no', 'received_from_name', 'received_from_designation',
                  'payee_signature_name', 'payee_address', 'payee_residence_cert_no', 'payee_residence_place',
                  'witness_signature_name', 'witness_address', 'witness_residence_cert_no', 'witness_residence_place']:
            if f in self.fields:
                self.fields[f].widget.attrs.update({'class': 'form-control'})
        self.fields['petty_cash_voucher'].widget.attrs.update({'class': 'form-control'})
        self.fields['petty_cash_voucher'].required = False
        self.fields['attached_image'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        # Help legacy field: optional
        self.fields['attached_image'].required = False
        self.fields['attached_image'].help_text = "Legacy single image (kept for compatibility). Use 'Add Images' for multiple."

    def clean_new_images(self):
        # Allow multiple files; view will use request.FILES.getlist so we just return the single value
        # Accept empty
        return self.cleaned_data.get('new_images')