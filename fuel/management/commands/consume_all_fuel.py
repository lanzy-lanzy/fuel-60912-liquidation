from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Consume exactly all remaining fuel to achieve 0.00L remaining'

    def handle(self, *args, **kwargs):
        # Get the precise total fuel allocation
        first_record = FuelConsumption.objects.first()
        if first_record and first_record.actual_fuel_price == 63.00:
            # v2 command was used
            total_fuel = 342978.36 / 63.00  # Precise calculation: 5444.100952380952...
            target_cost = 342978.36
        else:
            # Original command was used
            total_fuel = 7499.68
            target_cost = 311062.35
            
        # Calculate current total consumed and cost
        total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0
        
        remaining_fuel = total_fuel - total_consumed
        cost_difference = target_cost - total_cost
        
        if abs(remaining_fuel) > 0.000001 or abs(cost_difference) > 0.01:  # If there's any remaining fuel or cost difference
            self.stdout.write(
                self.style.WARNING(f'⚠️  Consuming exactly all remaining fuel: {remaining_fuel:.10f}L')
            )
            self.stdout.write(
                self.style.WARNING(f'⚠️  Adjusting cost by: ₱{cost_difference:.10f}')
            )
            
            # Get the last record and adjust it to consume the remaining fuel
            last_record = FuelConsumption.objects.order_by('-id').first()
            if last_record:
                # Directly update the record in the database to bypass all validation
                FuelConsumption.objects.filter(id=last_record.id).update(
                    total_liters=last_record.total_liters + remaining_fuel,
                    cost=last_record.cost + cost_difference  # Adjust cost to maintain target
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Consumed exactly all remaining fuel: {remaining_fuel:.10f}L')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Adjusted cost by: ₱{cost_difference:.10f}')
                )
                
                # Verify the result
                new_total_consumed = FuelConsumption.objects.aggregate(
                    Sum('total_liters')
                )['total_liters__sum'] or 0
                
                new_total_cost = FuelConsumption.objects.aggregate(
                    Sum('cost')
                )['cost__sum'] or 0
                
                new_remaining = total_fuel - new_total_consumed
                new_cost_difference = target_cost - new_total_cost
                self.stdout.write(
                    self.style.SUCCESS(f'Verification - Remaining fuel: {new_remaining:.10f}L')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Verification - Cost difference: ₱{new_cost_difference:.10f}')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ No remaining fuel to consume, and cost is exact')
            )