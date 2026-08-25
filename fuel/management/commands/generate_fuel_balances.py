from django.core.management.base import BaseCommand
from fuel.models import FuelConsumption
import random


class Command(BaseCommand):
    help = 'Generate and save fuel balance data (starting balance, finished balance, consumed) for all trips'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to generate balances for (YYYY-MM-DD format), or "all" for all dates',
            default='all'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate balances even if they already exist',
        )

    def handle(self, *args, **options):
        if options['date'] == 'all':
            records = FuelConsumption.objects.all()
        else:
            records = FuelConsumption.objects.filter(date=options['date'])
        
        # Filter out records that already have balances unless force flag is used
        if not options['force']:
            records = records.filter(starting_balance__isnull=True)
        
        if not records.exists():
            self.stdout.write(self.style.WARNING('No records found to process.'))
            return
        
        updated_count = 0
        
        # Order records by date, driver, and trip number
        records = records.order_by('date', 'driver', 'trip_number')
        
        # Track the ending balance for each driver per date
        driver_date_balance = {}
        
        for record in records:
            # Calculate balance in tank (same logic as gas_slip_print_view)
            driver_date_key = (record.driver.id, record.date)
            
            # For the first trip of the day for this driver, start with random balance between 7-10 liters
            if driver_date_key not in driver_date_balance:
                balance_in_tank = round(random.uniform(7.0, 10.0), 2)
            else:
                # For subsequent trips, use the ending balance from the previous trip
                balance_in_tank = driver_date_balance[driver_date_key]
            
            # The issued liters is the fuel dispensed from the station for this trip
            issued_liters = record.total_liters
            
            # Calculate new total in tank (balance + issued)
            total_in_tank = round(balance_in_tank + issued_liters, 2)
            
            # After the trip, some fuel is consumed, leaving a balance for the next trip
            # The ending balance should be between 7-10 liters (what remains after the trip)
            ending_balance = round(random.uniform(7.0, 10.0), 2)
            
            # Consumed = Total in tank - Ending balance
            consumed = round(total_in_tank - ending_balance, 2)
            
            # Store ending balance for next trip
            driver_date_balance[driver_date_key] = ending_balance
            
            # Save the balance data to the record
            record.starting_balance = balance_in_tank
            record.finished_balance = ending_balance
            record.consumed_liters = consumed
            record.save(update_fields=['starting_balance', 'finished_balance', 'consumed_liters'])
            
            updated_count += 1
            
            self.stdout.write(
                f"Driver: {record.driver.name}, Date: {record.date}, Trip #{record.trip_number} - "
                f"Start: {balance_in_tank:.2f}L, Issued: {issued_liters:.2f}L, "
                f"Consumed: {consumed:.2f}L, Finished: {ending_balance:.2f}L"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated and saved balance data for {updated_count} records')
        )
