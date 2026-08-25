from django.core.management.base import BaseCommand
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Update all fuel consumption records to use price 65.50/liter'

    def handle(self, *args, **kwargs):
        OLD_PRICE = 62.00
        NEW_PRICE = 65.50
        
        # Get all records with old price
        records = FuelConsumption.objects.filter(actual_fuel_price=OLD_PRICE)
        count = records.count()
        
        self.stdout.write(f'Found {count} records with price ₱{OLD_PRICE}/liter')
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No records to update!'))
            return
        
        # Update all records directly in database to bypass validation
        # For each record, recalculate cost = total_liters * NEW_PRICE
        updated_count = 0
        for record in records:
            # Calculate new cost
            new_cost = round(record.total_liters * NEW_PRICE, 2)
            
            # Update directly in database
            FuelConsumption.objects.filter(id=record.id).update(
                actual_fuel_price=NEW_PRICE,
                cost=new_cost
            )
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Updated {updated_count} records from ₱{OLD_PRICE} to ₱{NEW_PRICE}/liter'
            )
        )
        
        # Verify
        from django.db.models import Sum
        total_liters = FuelConsumption.objects.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
        total_cost = FuelConsumption.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        
        self.stdout.write(f'\nVerification:')
        self.stdout.write(f'Total Liters: {total_liters:.2f}L')
        self.stdout.write(f'Total Cost: ₱{total_cost:,.2f}')
        self.stdout.write(f'Average Price: ₱{total_cost / total_liters:.2f}/liter')
