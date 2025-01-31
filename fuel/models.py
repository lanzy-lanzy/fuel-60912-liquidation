from django.db import models
from django.core.exceptions import ValidationError
import datetime
import random

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
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    date = models.DateField()
    number_of_trips = models.PositiveIntegerField()
    purpose = models.CharField(max_length=200, help_text="Trip purpose/description")
    total_liters = models.FloatField()
    cost = models.FloatField()

    FUEL_PRICE = 56.50
    TOTAL_FUEL_ALLOCATION = 7499.68
    MIN_LITERS_PER_TRIP = 15
    MAX_LITERS_PER_TRIP = 25

    @property
    def vehicle(self):
        return self.driver.vehicle

    class Meta:
        unique_together = ('driver', 'date')
        verbose_name = "Fuel Consumption"
        verbose_name_plural = "Fuel Consumptions"

    def clean(self):
        super().clean()
        start_date = datetime.date(2024, 10, 13)
        end_date = datetime.date(2024, 12, 31)
        
        if not (start_date <= self.date <= end_date):
            raise ValidationError(
                f"Date must be between {start_date.strftime('%Y-%m-%d')} "
                f"and {end_date.strftime('%Y-%m-%d')}"
            )

    def save(self, *args, **kwargs):
        if not self.total_liters:
            self._calculate_fuel_usage()
        
        self.clean()
        self._check_fuel_limits()
        super().save(*args, **kwargs)

    def _calculate_fuel_usage(self):
        if not self.number_of_trips:
            raise ValidationError("Number of trips must be set")

        total_liters = sum(
            round(random.uniform(self.MIN_LITERS_PER_TRIP, self.MAX_LITERS_PER_TRIP), 2)
            for _ in range(self.number_of_trips)
        )

        self.total_liters = round(total_liters, 2)
        self.cost = round(self.total_liters * self.FUEL_PRICE, 2)

    def _check_fuel_limits(self):
        queryset = FuelConsumption.objects.exclude(pk=self.pk)
        total_consumed = queryset.aggregate(
            models.Sum('total_liters')
        )['total_liters__sum'] or 0

        if self.pk:
            old_instance = FuelConsumption.objects.get(pk=self.pk)
            total_consumed -= old_instance.total_liters

        proposed_total = total_consumed + self.total_liters

        if proposed_total > self.TOTAL_FUEL_ALLOCATION:
            remaining_fuel = self.TOTAL_FUEL_ALLOCATION - total_consumed
            raise ValidationError(
                f"Insufficient fuel! Available: {remaining_fuel:.2f}L, "
                f"Requested: {self.total_liters:.2f}L"
            )

    def __str__(self):
        return (f"{self.driver} | {self.date.strftime('%Y-%m-%d')} | "
                f"{self.number_of_trips} trips | {self.total_liters}L")