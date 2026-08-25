from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption, Driver

class Command(BaseCommand):
    help = 'Check dashboard values'

    def handle(self, *args, **kwargs):
        # Calculate fuel statistics
        total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        # Get the actual fuel price from the first record to determine which command was used
        first_record = FuelConsumption.objects.first()
        if first_record and first_record.actual_fuel_price == 63.00:
            # v2 command was used
            total_fuel = 342978.36 / 63.00  # Precise calculation: 5444.100952380952...
        else:
            # Original command was used
            total_fuel = 5017.135  # 311062.35 / 62.00
        
        remaining_fuel = total_fuel - total_consumed
        total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0

        self.stdout.write(
            self.style.SUCCESS(f'Total Consumed: {round(total_consumed, 2)} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Remaining Fuel: {round(remaining_fuel, 2)} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total Cost: ₱{round(total_cost, 2):,}')
        )