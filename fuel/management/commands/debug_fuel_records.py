from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Debug fuel records to check for inconsistencies'

    def handle(self, *args, **kwargs):
        records = FuelConsumption.objects.all().order_by('-id')
        
        total_liters = 0
        total_cost = 0
        
        for record in records:
            total_liters += record.total_liters
            total_cost += record.cost
            
        # Also get the totals from the database aggregation
        db_total_liters = FuelConsumption.objects.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
        db_total_cost = FuelConsumption.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Total liters (calculated): {total_liters:.2f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cost (calculated): ₱{total_cost:,.2f}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total liters (DB aggregate): {db_total_liters:.2f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cost (DB aggregate): ₱{db_total_cost:,.2f}')
        )
        
        # Check the last few records
        self.stdout.write('\nLast 5 records:')
        for record in records[:5]:
            expected_cost = record.total_liters * record.actual_fuel_price
            self.stdout.write(
                f'ID: {record.id}, Liters: {record.total_liters:.2f}L, Cost: ₱{record.cost:.2f}, '
                f'Actual Price: ₱{record.actual_fuel_price:.2f}, Expected Cost: ₱{expected_cost:.2f}, '
                f'Difference: ₱{abs(record.cost - expected_cost):.2f}'
            )
            
        # Check if there are any records with inconsistent pricing
        inconsistent_records = []
        for record in records:
            expected_cost = record.total_liters * record.actual_fuel_price
            if abs(record.cost - expected_cost) > 0.01:  # More than 1 cent difference
                inconsistent_records.append(record)
                
        if inconsistent_records:
            self.stdout.write(f'\nFound {len(inconsistent_records)} records with cost/liter inconsistencies:')
            for record in inconsistent_records[:10]:  # Show first 10
                expected_cost = record.total_liters * record.actual_fuel_price
                self.stdout.write(
                    f'ID: {record.id}, Liters: {record.total_liters:.2f}L, Cost: ₱{record.cost:.2f}, '
                    f'Actual Price: ₱{record.actual_fuel_price:.2f}, Expected Cost: ₱{expected_cost:.2f}, '
                    f'Difference: ₱{abs(record.cost - expected_cost):.2f}'
                )