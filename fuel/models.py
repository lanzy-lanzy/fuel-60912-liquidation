from django.db import models
from django.core.exceptions import ValidationError
import datetime
import random

class Driver(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"

class FuelConsumption(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    date = models.DateField()
    number_of_trips = models.PositiveIntegerField()
    purpose = models.CharField(max_length=200, help_text="Trip purpose/description")
    total_liters = models.FloatField(editable=False)
    cost = models.FloatField(editable=False)

    class Meta:
        unique_together = ('driver', 'date')
        verbose_name = "Fuel Consumption"
        verbose_name_plural = "Fuel Consumptions"

    def clean(self):
        """Validate date is within operational period"""
        super().clean()
        start_date = datetime.date(2024, 10, 13)
        end_date = datetime.date(2024, 12, 31)
        if not (start_date <= self.date <= end_date):
            raise ValidationError(
                f"Date must be between {start_date.strftime('%Y-%m-%d')} "
                f"and {end_date.strftime('%Y-%m-%d')}"
            )

    def save(self, *args, **kwargs):
        """Custom save method with fuel calculations and validations"""
        # Generate fuel consumption values
        self._calculate_fuel_usage()
        
        # Validate date range
        self.clean()
        
        # Check fuel limits
        self._check_fuel_limits()
        
        super().save(*args, **kwargs)

    def _calculate_fuel_usage(self):
        """Calculate fuel consumption and cost"""
        if self.number_of_trips is None:
            raise ValidationError("Number of trips must be set")

        # Calculate random fuel consumption per trip, ensuring it does not exceed 25 liters
        total_liters = 0.0
        for _ in range(self.number_of_trips):
            total_liters += round(random.uniform(15, 25), 2)  # Ensure max is 25 liters

        # Calculate cost and adjust if it exceeds 1500
        cost = total_liters * 56.50
        if cost > 1500:
            total_liters = 1500 / 56.50

        self.total_liters = round(total_liters, 2)
        self.cost = round(self.total_liters * 56.50, 2)

    def _check_fuel_limits(self):
        """Ensure total fuel consumption doesn't exceed available stock"""
        # Get existing consumption excluding current instance
        queryset = FuelConsumption.objects.exclude(pk=self.pk)
        total_consumed = queryset.aggregate(
            models.Sum('total_liters')
        )['total_liters__sum'] or 0

        # Account for updates
        if self.pk:
            old_instance = FuelConsumption.objects.get(pk=self.pk)
            total_consumed -= old_instance.total_liters

        proposed_total = total_consumed + self.total_liters

        if proposed_total > 7499.68:
            raise ValidationError(
                f"Fuel limit exceeded! Available: 7499.68L, "
                f"Attempted: {proposed_total:.2f}L"
            )

    def __str__(self):
        return (f"{self.driver} | {self.date.strftime('%Y-%m-%d')} | "
                f"{self.number_of_trips} trips | {self.total_liters}L")