from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Debug remaining fuel calculation'

    def handle(self, *args, **kwargs):
        # Get the actual fuel price from the first record to determine which command was used
        first_record = FuelConsumption.objects.first()
        if first_record and first_record.actual_fuel_price == 63.00:
            # v2 command was used
            total_fuel = 5444.10  # 342978.36 / 63.00
        else:
            # Original command was used
            total_fuel = 7499.68
            
        # Calculate fuel statistics
        total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        remaining_fuel = total_fuel - total_consumed
        total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0

        self.stdout.write(
            self.style.SUCCESS(f'Total fuel allocation: {total_fuel:.2f} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total consumed: {total_consumed:.2f} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Remaining fuel: {remaining_fuel:.2f} L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cost: ₱{total_cost:,.2f}')
        )
        
        # Check the last record
        last_record = FuelConsumption.objects.order_by('-id').first()
        if last_record:
            self.stdout.write(
                self.style.SUCCESS(f'\nLast record details:')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  ID: {last_record.id}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  Liters: {last_record.total_liters:.2f} L')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  Cost: ₱{last_record.cost:.2f}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  Actual fuel price: ₱{last_record.actual_fuel_price:.2f}')
            )
            expected_cost = last_record.total_liters * last_record.actual_fuel_price
            self.stdout.write(
                self.style.SUCCESS(f'  Expected cost: ₱{expected_cost:.2f}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  Difference: ₱{abs(last_record.cost - expected_cost):.2f}')
            )