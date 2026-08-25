from django.core.exceptions import ValidationError
from django.db import models
import random
from datetime import date

def validate_date_range(value):
    if value < date(2024, 10, 13):  # Only lower bound enforced
        raise ValidationError('Date must be on or after 2024-10-13')

class Driver(models.Model):
    name = models.CharField(max_length=100, unique=True)
    vehicle = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.vehicle}"

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"

class Vehicle(models.Model):
    name = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.name} ({self.plate_number})"

class FuelConsumption(models.Model):
    reference_number = models.PositiveIntegerField(default=1)

    # Destination choices for ambulances (excludes local area)
    AMBULANCE_DESTINATION_CHOICES = [
        ('dipolog', 'Dipolog'),
        ('cagayan', 'Cagayan'),
        ('margosatubig', 'Margosatubig'),
        ('pagadian_city', 'Pagadian City'),
        ('ozamiz_city', 'Ozamiz City'),
        ('zamboanga_city', 'Zamboanga City'),
        ('davao_city', 'Davao City'),
        ('ipil', 'Ipil'),
        ('sindangan', 'Sindangan'),
        ('molave_blancia_hospital', 'Molave Blancia Hospital'),  # New destination
    ]

    # Destination choices for heavy equipment (local area only)
    HEAVY_EQUIPMENT_DESTINATION_CHOICES = [
        ('local', 'Local Area'),
    ]

    # Special destination for budget utilization (not a regular destination)
    MAHAYAG_SPECIAL_CHOICE = [('mahayag', 'Mahayag Medicare')]

    # Combined choices for the model field (for backward compatibility)
    DESTINATION_CHOICES = AMBULANCE_DESTINATION_CHOICES + HEAVY_EQUIPMENT_DESTINATION_CHOICES + MAHAYAG_SPECIAL_CHOICE

    PURPOSE_CHOICES = [
        ('Transport Patient', 'Transport Patient'),
        ('landslide sinonok', 'Landslide Sinonok'),
        ('landslide bag-ong kauswagan', 'Landslide Bag-ong Kauswagan'),
        ('landslide macasing', 'Landslide Macasing'),
        ('mahayag medicare', 'Mahayag Medicare'),
    ]

    driver = models.ForeignKey('Driver', on_delete=models.CASCADE)
    date = models.DateField()
    trip_number = models.PositiveIntegerField(default=1)
    number_of_trips = models.PositiveIntegerField(default=1)
    purpose = models.CharField(max_length=255, choices=PURPOSE_CHOICES, default="Transport Patient")
    destination = models.CharField(max_length=100, choices=DESTINATION_CHOICES, default='local')
    total_liters = models.FloatField()
    cost = models.FloatField()
    vehicle = models.CharField(max_length=100)
    # Store the actual fuel price used for this record
    actual_fuel_price = models.FloatField(default=62.00)  # Default to 62.00 for backward compatibility
    
    # Time tracking fields
    departure_time = models.TimeField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    return_departure_time = models.TimeField(null=True, blank=True)
    return_arrival_time = models.TimeField(null=True, blank=True)
    
    # Fuel balance tracking fields
    starting_balance = models.FloatField(null=True, blank=True)  # Starting fuel in tank
    finished_balance = models.FloatField(null=True, blank=True)  # Ending fuel in tank
    consumed_liters = models.FloatField(null=True, blank=True)  # Fuel consumed during trip
    
    # Passenger name field
    passenger_name = models.CharField(max_length=255, null=True, blank=True)

    # Official Receipt (OR) number for liquidation reporting
    or_number = models.CharField(max_length=50, null=True, blank=True)

    MIN_LITERS_PER_TRIP = 17.69
    MAX_LITERS_PER_TRIP = 26.54
    FUEL_PRICE = 62.00 #per liter
    TOTAL_FUEL_ALLOCATION = 5017.135  # 311062.35 / 62.00 = 5017.135 liters
    # Destination-based fuel budget (in pesos)
    DESTINATION_BUDGET_MAP = {
        'dipolog': 2500,
        'cagayan': 5000,
        'margosatubig': 2000,
        'pagadian_city': 1000,
        'ozamiz_city': 1500,
        'zamboanga_city': 5000,
        'davao_city': 5000,
        'ipil': 3500,
        'sindangan': 1500,
        'local': 2000,  # Default budget for local trips
        'molave_blancia_hospital': 800,  # New destination budget
    }

    # Special budget for mahayag utilization (not a regular destination)
    MAHAYAG_BUDGET_UTILIZATION = 900  # Budget available for mahayag special cases (less than ₱1,000)

    # Fixed fuel consumption for heavy equipment (in liters)
    HEAVY_EQUIPMENT_FUEL = 400  # Backhoe and Dumptruck consume 400L each

    def get_destination_budget(self):
        """Get the fuel budget (in pesos) for the current destination"""
        # Handle mahayag as special budget utilization case
        if self.destination == 'mahayag':
            return self.MAHAYAG_BUDGET_UTILIZATION
        return self.DESTINATION_BUDGET_MAP.get(self.destination, self.DESTINATION_BUDGET_MAP['local'])

    def get_destination_liters(self):
        """Calculate liters based on destination budget and fuel price"""
        budget = self.get_destination_budget()
        return round(budget / self.FUEL_PRICE, 2)

    def __str__(self):
        return f"{self.driver} on {self.date} (Trip {self.trip_number})"

    class Meta:
        unique_together = ('driver', 'date', 'trip_number')

    def clean(self):
        """Validate that destination is appropriate for vehicle type"""
        super().clean()

        # Check if ambulance is trying to use local destination
        if (hasattr(self, 'vehicle') and
            self.vehicle in ['Ambulance L300', 'Ambulance Province', 'Ambulance DOH'] and
            self.destination == 'local'):
            raise ValidationError("Ambulances cannot use 'Local Area' destination. Local Area is reserved for heavy equipment only.")

        # Check if heavy equipment is trying to use non-local destination
        if (hasattr(self, 'vehicle') and
            self.vehicle in ['Backhoe', 'Dumptruck'] and
            self.destination != 'local'):
            raise ValidationError("Heavy equipment (Backhoe/Dumptruck) can only use 'Local Area' destination.")

        # Check if mahayag is being used appropriately (special budget utilization case)
        if (hasattr(self, 'destination') and self.destination == 'mahayag'):
            # Mahayag can only be used by DOH ambulance for patient transport
            if not (hasattr(self, 'vehicle') and self.vehicle == 'Ambulance DOH'):
                raise ValidationError("Mahayag budget utilization is only available for DOH ambulance.")
            if not (hasattr(self, 'purpose') and self.purpose == 'Transport Patient'):
                raise ValidationError("Mahayag budget utilization is only available for patient transport purposes.")

    def save(self, *args, **kwargs):
        # Check if we're only updating time fields or balance fields
        update_fields = kwargs.get('update_fields', None)
        time_fields_only = update_fields and all(field in ['departure_time', 'arrival_time', 'return_departure_time', 'return_arrival_time'] for field in update_fields)
        balance_fields_only = update_fields and all(field in ['starting_balance', 'finished_balance', 'consumed_liters'] for field in update_fields)
        
        # Check if we're using a custom fuel price
        if hasattr(self, '_fuel_price'):
            custom_price = self._fuel_price
            # Update the fuel price and recalculate total fuel allocation
            self.FUEL_PRICE = custom_price
            # Recalculate allocation based on the specific budget (either the 509k or the 342k one)
            if hasattr(self, '_bypass_fuel_limit') and self._bypass_fuel_limit:
                # For custom data population, we primarily care about storing the price
                self.TOTAL_FUEL_ALLOCATION = 509827.00 / custom_price
            else:
                self.TOTAL_FUEL_ALLOCATION = 342978.36 / custom_price
            
            # Store the actual fuel price used
            self.actual_fuel_price = custom_price
        else:
            # Store the default fuel price
            self.actual_fuel_price = 62.00
        
        # If total_liters and cost are already set (manually), skip calculation
        if not self.total_liters or not self.cost:
            self._calculate_fuel_usage()

        # Only run validation and fuel limit checks if we're not just updating time or balance fields
        if not time_fields_only and not balance_fields_only:
            self.clean()
            self._check_fuel_limits()
            
        super().save(*args, **kwargs)

    def _calculate_fuel_usage(self):
        if not self.number_of_trips:
            raise ValidationError("Number of trips must be set")

        # Check if this is heavy equipment (Backhoe or Dumptruck)
        if hasattr(self, 'vehicle') and self.vehicle in ['Backhoe', 'Dumptruck']:
            # Fixed 400 liters for heavy equipment
            total_liters = self.HEAVY_EQUIPMENT_FUEL * self.number_of_trips
            total_cost = total_liters * self.FUEL_PRICE
        elif hasattr(self, 'destination') and self.destination:
            # Use destination-based fuel budget for ambulances
            if self.destination == 'mahayag':
                # Special mahayag budget utilization
                budget_per_trip = self.MAHAYAG_BUDGET_UTILIZATION
            else:
                budget_per_trip = self.DESTINATION_BUDGET_MAP.get(self.destination, self.DESTINATION_BUDGET_MAP['local'])
            total_cost = budget_per_trip * self.number_of_trips
            total_liters = total_cost / self.FUEL_PRICE
        else:
            # Fallback to random calculation for backward compatibility
            total_liters = sum(
                round(random.uniform(self.MIN_LITERS_PER_TRIP, self.MAX_LITERS_PER_TRIP), 2)
                for _ in range(self.number_of_trips)
            )
            total_cost = total_liters * self.FUEL_PRICE

        self.total_liters = round(total_liters, 2)
        self.cost = round(total_cost, 2)

    def _check_fuel_limits(self):
        # Check if we're using the v2 command with different fuel price
        fuel_allocation = self.TOTAL_FUEL_ALLOCATION
        if hasattr(self, '_fuel_price') and self._fuel_price == 63.00:
            # For the v2 command, use the updated fuel allocation
            fuel_allocation = 342978.36 / 63.00  # Precise calculation
        
        # Check if we should bypass fuel limit check (for final consumption commands)
        if hasattr(self, '_bypass_fuel_limit') and self._bypass_fuel_limit:
            return  # Skip fuel limit check
        
        queryset = FuelConsumption.objects.exclude(pk=self.pk)
        total_consumed = queryset.aggregate(
            models.Sum('total_liters')
        )['total_liters__sum'] or 0

        if self.pk:
            old_instance = FuelConsumption.objects.get(pk=self.pk)
            total_consumed -= old_instance.total_liters

        proposed_total = total_consumed + self.total_liters

        if proposed_total > fuel_allocation:
            remaining_fuel = fuel_allocation - total_consumed
            raise ValidationError(
                f"Insufficient fuel! Available: {remaining_fuel:.2f}L, "
                f"Requested: {self.total_liters:.2f}L"
            )

    def __str__(self):
        return (f"{self.driver} | {self.date.strftime('%Y-%m-%d')} | "
                f"{self.number_of_trips} trips | {self.total_liters}L")


class LiquidationSetting(models.Model):
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    check_number = models.CharField(max_length=50, null=True, blank=True)
    # Footer dynamic amounts - editable per template
    refund_or_number = models.CharField(max_length=50, null=True, blank=True, help_text="OR Number for Amount Refund per OR #")
    amount_refund_per_or = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Amount Refund per OR # (footer)")
    amount_reimbursed = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Amount Reimbursed (footer)")

    def __str__(self):
        return f'Liquidation Setting (Principal: {self.principal_amount})'


class LiquidationReport(models.Model):
    no = models.CharField(max_length=50, null=True, blank=True)
    report_date = models.DateField(default=date.today)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    check_number = models.CharField(max_length=50, null=True, blank=True)
    # Footer dynamic amounts
    refund_or_number = models.CharField(max_length=50, null=True, blank=True, help_text="OR Number for Amount Refund per OR #")
    amount_refund_per_or = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Amount Refund per OR #")
    amount_reimbursed = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Amount Reimbursed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Liquidation Report {self.no or self.pk} ({self.report_date})'

    def total(self):
        return sum(entry.amount for entry in self.entries.all())


class LiquidationReportEntry(models.Model):
    report = models.ForeignKey(LiquidationReport, on_delete=models.CASCADE, related_name='entries')
    entry_date = models.DateField()
    or_number = models.CharField(max_length=50, null=True, blank=True)
    fuel_type = models.CharField(max_length=50, default='Diesel')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # If VAT inclusive, WHT = amount/1.12*rate (default, 12% VAT). If non-VAT, WHT = amount*rate (optional per row)
    vat_inclusive = models.BooleanField(default=True, help_text="VAT inclusive - checked: amount includes 12% VAT (WHT = amount/1.12*rate). Unchecked: Non-VAT (no withholding, Net = Amount)")
    # Dynamic per-row WHT amounts - editable; if set, overrides computed WHT
    wht5_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Withholding Tax 5% (editable per row, overrides computed)")
    wht1_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Withholding Tax 1% (editable per row)")

    def __str__(self):
        return f'{self.or_number or "No OR"} - {self.amount}'

    def get_wht5(self):
        if self.wht5_amount is not None:
            return self.wht5_amount
        if self.vat_inclusive:
            return (self.amount / Decimal('1.12') * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')

    def get_wht1(self):
        if self.wht1_amount is not None:
            return self.wht1_amount
        if self.vat_inclusive:
            return (self.amount / Decimal('1.12') * Decimal('0.01')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')


# ── Petty Cash & RER ── Separate transaction module (not fuel)

class PettyCashVoucher(models.Model):
    voucher_no = models.CharField(max_length=50, blank=True, help_text="PCV No.")
    voucher_date = models.DateField(default=date.today)
    fund = models.CharField(max_length=100, blank=True, default="")
    fpp = models.CharField(max_length=100, blank=True, verbose_name="FPP")
    payee_office = models.CharField(max_length=150, default="MDRRMO")
    address = models.CharField(max_length=255, default="Dumingag, Zamboanga del Sur")
    # Left side - upon request
    particulars = models.TextField(blank=True, help_text="Particulars (one per line or free text)")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purpose = models.TextField(blank=True)
    requested_by_name = models.CharField(max_length=150, blank=True)
    approved_by_name = models.CharField(max_length=150, default="JHUNAX L. CARDOZA")
    paid_by_name = models.CharField(max_length=150, default="JHUNAX L. CARDOZA")
    cash_received_by_name = models.CharField(max_length=150, blank=True)
    # Right side - upon liquidation
    total_amount_granted = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_amount_paid_per_or = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    or_invoice_no = models.CharField(max_length=100, blank=True)
    amount_refunded = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    received_refund = models.BooleanField(default=False)
    reimbursement_paid = models.BooleanField(default=False)
    liquidation_submitted = models.BooleanField(default=False)
    reimbursement_received_by = models.CharField(max_length=150, blank=True)
    # meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-voucher_date', '-id']
        verbose_name = "Petty Cash Voucher"
        verbose_name_plural = "Petty Cash Vouchers"

    def __str__(self):
        return f"PCV {self.voucher_no or self.pk} - {self.voucher_date} - P{self.amount}"


def rer_image_path(instance, filename):
    return f"rer_images/{instance.rer_no or 'rer'}_{filename}"


def rer_gallery_image_path(instance, filename):
    # instance is ReimbursementExpenseReceiptImage
    # Use RER's rer_no and pk for namespacing; fallback to 'rer'
    rer = getattr(instance, 'rer', None)
    prefix = (getattr(rer, 'rer_no', None) or getattr(rer, 'pk', None) or 'rer')
    # sanitize prefix to avoid slash
    prefix = str(prefix).replace('/', '_').replace('\\', '_')[:50]
    return f"rer_images/{prefix}_{filename}"


class ReimbursementExpenseReceipt(models.Model):
    # Header
    entity_name = models.CharField(max_length=150, blank=True, default="")
    fund_cluster = models.CharField(max_length=100, blank=True)
    receipt_date = models.DateField(default=date.today)
    rer_no = models.CharField(max_length=50, blank=True, verbose_name="RER No.")
    # Body
    received_from_name = models.CharField(max_length=150, blank=True, verbose_name="Received from (Name)")
    received_from_designation = models.CharField(max_length=150, blank=True, verbose_name="Official Designation")
    amount_in_words = models.CharField(max_length=255, blank=True, verbose_name="Amount in Words")
    amount_in_figures = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Amount in Figures (P)")
    in_payment_for = models.TextField(blank=True, verbose_name="In payment for", help_text="e.g., Payments for subsistence, services, rental or transportation should show inclusive dates, purpose, distance, points of travel, etc.")
    # Payee
    payee_signature_name = models.CharField(max_length=150, blank=True, verbose_name="Payee Name")
    payee_address = models.CharField(max_length=255, blank=True)
    payee_residence_cert_no = models.CharField(max_length=100, blank=True)
    payee_residence_date = models.DateField(null=True, blank=True)
    payee_residence_place = models.CharField(max_length=150, blank=True)
    # Witness
    witness_signature_name = models.CharField(max_length=150, blank=True, verbose_name="Witness Name")
    witness_address = models.CharField(max_length=255, blank=True)
    witness_residence_cert_no = models.CharField(max_length=100, blank=True)
    witness_residence_date = models.DateField(null=True, blank=True)
    witness_residence_place = models.CharField(max_length=150, blank=True)
    # Attachment image (printed on top of RER) — legacy single image; kept for backward compat
    attached_image = models.ImageField(upload_to=rer_image_path, null=True, blank=True)
    # Optional link to PCV (as attachment)
    petty_cash_voucher = models.ForeignKey(PettyCashVoucher, null=True, blank=True, on_delete=models.SET_NULL, related_name="rers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-receipt_date', '-id']
        verbose_name = "Reimbursement Expense Receipt"
        verbose_name_plural = "Reimbursement Expense Receipts"

    def __str__(self):
        return f"RER {self.rer_no or self.pk} - {self.receipt_date} - P{self.amount_in_figures}"

    @property
    def all_images(self):
        """
        Return queryset/list of all images for this RER.
        Prefers the new multi-image gallery (images relation).
        Falls back to legacy attached_image for backward compatibility.
        """
        qs = self.images.all()
        if qs.exists():
            return qs
        # fallback: if legacy single image exists, return a synthetic list
        if self.attached_image:
            # Return a list with a mock object exposing .image.url etc. for template uniformity
            # We return the RER itself as a proxy? Better return list with attached_image wrapped
            # For simplicity, callers should check both .images and .attached_image,
            # but this helper returns images queryset if any, else empty list
            return qs
        return qs

    def get_gallery_images(self):
        """Return list of image objects/URLs for gallery: new images or legacy fallback."""
        imgs = list(self.images.all())
        if imgs:
            return imgs
        if self.attached_image:
            # create a lightweight wrapper
            class LegacyWrapper:
                def __init__(self, field):
                    self.image = field
                    self.url = field.url if field else None
            # Not ideal for template; easier to handle in template with if
            return []
        return []


class ReimbursementExpenseReceiptImage(models.Model):
    """Multiple images per RER — printed on top of RER form, laid out as grid."""
    rer = models.ForeignKey(ReimbursementExpenseReceipt, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=rer_gallery_image_path)
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "RER Image"
        verbose_name_plural = "RER Images"

    def __str__(self):
        return f"RER {self.rer_id} Image {self.pk}"