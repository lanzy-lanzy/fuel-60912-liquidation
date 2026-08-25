from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Check total fuel consumption and cost'

    def handle(self, *args, **kwargs):
        total_liters = FuelConsumption.objects.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
        total_cost = FuelConsumption.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Total liters consumed: {total_liters:.2f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cost: ₱{total_cost:,.2f}')
        )
        
        # Check if we're using the v2 command data (based on actual_fuel_price)
        first_record = FuelConsumption.objects.first()
        if first_record and first_record.actual_fuel_price == 63.00:
            expected_liters = 342978.36 / 63.00  # 5444.10 liters
            self.stdout.write(
                self.style.SUCCESS(f'Expected liters (v2): {expected_liters:.2f}L')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Difference: {abs(total_liters - expected_liters):.2f}L')
            )