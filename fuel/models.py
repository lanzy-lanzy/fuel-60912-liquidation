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
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE)
    date = models.DateField()
    trip_number = models.PositiveIntegerField(default=1)
    number_of_trips = models.PositiveIntegerField(default=1)
    purpose = models.CharField(max_length=255, default="Transport Patient")
    total_liters = models.FloatField()
    cost = models.FloatField()
    vehicle = models.CharField(max_length=100)  # Add this new field
    MIN_LITERS_PER_TRIP = 17.69
    MAX_LITERS_PER_TRIP = 26.54
    FUEL_PRICE = 56.50 #per liter
    TOTAL_FUEL_ALLOCATION = 7499.68  # 423731.92 / 56.50 ≈ 7500 liters

    def __str__(self):
        return f"{self.driver} on {self.date} (Trip {self.trip_number})"

    class Meta:
        unique_together = ('driver', 'date', 'trip_number')

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