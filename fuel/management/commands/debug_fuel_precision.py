from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Debug fuel precision to see exact values'

    def handle(self, *args, **kwargs):
        # Get the actual fuel price from the first record to determine which command was used
        first_record = FuelConsumption.objects.first()
        if first_record and first_record.actual_fuel_price == 63.00:
            # v2 command was used
            total_fuel = 342978.36 / 63.00  # Precise calculation: 5444.100952380952...
        else:
            # Original command was used
            total_fuel = 5017.135  # 311062.35 / 62.00
            
        # Calculate fuel statistics with high precision
        total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        remaining_fuel = total_fuel - total_consumed
        total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0

        self.stdout.write(
            self.style.SUCCESS(f'Total fuel allocation: {total_fuel:.10f} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total consumed: {total_consumed:.10f} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Remaining fuel: {remaining_fuel:.10f} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cost: ₱{total_cost:.10f}')
        )
        
        # Check the last few records
        last_records = FuelConsumption.objects.order_by('-id')[:3]
        self.stdout.write(
            self.style.SUCCESS(f'\nLast 3 records:')
        )
        for record in last_records:
            self.stdout.write(
                self.style.SUCCESS(f'  ID: {record.id}, Liters: {record.total_liters:.10f} L, Cost: ₱{record.cost:.10f}')
            )