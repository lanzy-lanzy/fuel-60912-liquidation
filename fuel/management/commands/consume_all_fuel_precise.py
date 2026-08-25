from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Consume exactly all remaining fuel to achieve 0.00L remaining with precise calculation'

    def handle(self, *args, **kwargs):
        # Get the precise total fuel allocation
        first_record = FuelConsumption.objects.first()
        if first_record and first_record.actual_fuel_price == 63.00:
            # v2 command was used
            total_fuel = 342978.36 / 63.00  # Precise calculation: 5444.100952380952...
            target_cost = 342978.36
        else:
            # Original command was used
            total_fuel = 5017.135  # 311062.35 / 62.00
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
                self.style.WARNING(f'Remaining fuel: {remaining_fuel:.10f}L (₱{remaining_fuel * (first_record.actual_fuel_price if first_record else 62.00):.2f})')
            )
            
            # Get the last record to modify or create a new one
            last_record = FuelConsumption.objects.order_by('-id').first()
            
            if last_record:
                # Adjust the last record to consume exactly all fuel
                new_liters = last_record.total_liters + remaining_fuel
                new_cost = last_record.cost + cost_difference
                
                # Update the last record
                last_record.total_liters = new_liters
                last_record.cost = new_cost
                # Set attribute to bypass fuel limit check
                last_record._bypass_fuel_limit = True
                last_record.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Adjusted last record to consume exactly all fuel')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   Added {remaining_fuel:.10f}L to last record')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('No records found to adjust')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('All fuel already consumed exactly')
            )
        
        # Final verification
        final_total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        final_total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0
        
        final_remaining = total_fuel - final_total_consumed
        
        self.stdout.write(
            self.style.SUCCESS(f'Final total consumed: {final_total_consumed:.10f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Final remaining fuel: {final_remaining:.10f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Final total cost: ₱{final_total_cost:.2f}')
        )
        
        if abs(final_remaining) < 0.000001:
            self.stdout.write(
                self.style.SUCCESS('✅ All fuel has been consumed exactly!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Small amount of fuel remaining: {final_remaining:.10f}L')
            )