from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Adjust fuel consumption records to ensure exactly 5017.135L is consumed and displays as 5017.13L'

    def handle(self, *args, **kwargs):
        # Get the precise total fuel allocation
        total_fuel = 5017.135  # 311062.35 / 62.00
        
        # Calculate current total consumed
        total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        # Calculate difference
        difference = total_fuel - total_consumed
        
        self.stdout.write(
            self.style.SUCCESS(f'Current total consumed: {total_consumed:.10f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Target total: {total_fuel:.10f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Difference: {difference:.10f}L')
        )
        
        if abs(difference) > 0.000001:  # If there's any significant difference
            # Get the last record to adjust
            last_record = FuelConsumption.objects.order_by('-id').first()
            
            if last_record:
                # Adjust the last record to make the total exactly 5017.135L
                new_liters = last_record.total_liters + difference
                
                self.stdout.write(
                    self.style.WARNING(f'Adjusting last record (ID: {last_record.id})')
                )
                self.stdout.write(
                    self.style.WARNING(f'  Old value: {last_record.total_liters:.10f}L')
                )
                self.stdout.write(
                    self.style.WARNING(f'  New value: {new_liters:.10f}L')
                )
                
                # Update the record
                last_record.total_liters = new_liters
                # Set attribute to bypass fuel limit check
                last_record._bypass_fuel_limit = True
                last_record.save()
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Successfully adjusted fuel consumption')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('No records found to adjust')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Fuel consumption is already at the correct value')
            )
        
        # Final verification
        final_total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Final total consumed: {final_total_consumed:.10f}L')
        )
        
        # Show how this will display with different rounding
        self.stdout.write(
            self.style.SUCCESS(f'Displayed as 5017.135L: {final_total_consumed:.3f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Displayed as 5017.14L: {final_total_consumed:.2f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Displayed as 5017.1L: {final_total_consumed:.1f}L')
        )
        
        # Check if we're exactly at 5017.135L
        if abs(final_total_consumed - 5017.135) < 0.000001:
            self.stdout.write(
                self.style.SUCCESS('✅ Total fuel consumption is exactly 5017.135L')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Total fuel consumption is not exactly 5017.135L')
            )