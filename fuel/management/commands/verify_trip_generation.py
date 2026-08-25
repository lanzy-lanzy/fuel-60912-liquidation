from django.core.management.base import BaseCommand
from fuel.models import FuelConsumption, Driver

class Command(BaseCommand):
    help = 'Verify trip generation pattern'

    def handle(self, *args, **kwargs):
        # Check a sample of records to verify trip generation pattern
        records = FuelConsumption.objects.order_by('date', 'driver_id', 'trip_number')
        
        self.stdout.write("First 20 records:")
        for record in records[:20]:
            self.stdout.write(
                f"Date: {record.date}, Driver: {record.driver.name}, "
                f"Trip #: {record.trip_number}, Trips: {record.number_of_trips}, "
                f"L: {record.total_liters:.2f}, Cost: ₱{record.cost:.2f}"
            )
            
        # Check if we have 2 trips per driver per day in a sample
        self.stdout.write("\nChecking trip pattern for a specific date:")
        sample_date = records.first().date if records.exists() else None
        if sample_date:
            day_records = FuelConsumption.objects.filter(date=sample_date).order_by('driver_id')
            driver_trip_counts = {}
            for record in day_records:
                driver_name = record.driver.name
                if driver_name not in driver_trip_counts:
                    driver_trip_counts[driver_name] = 0
                driver_trip_counts[driver_name] += record.number_of_trips
                
            for driver, trip_count in driver_trip_counts.items():
                self.stdout.write(f"Driver {driver}: {trip_count} trips")
                
        # Check trip numbering for a specific driver
        self.stdout.write("\nChecking trip numbering for a specific driver:")
        sample_driver = Driver.objects.first()
        if sample_driver:
            driver_records = FuelConsumption.objects.filter(driver=sample_driver).order_by('date', 'trip_number')
            for record in driver_records[:10]:
                self.stdout.write(
                    f"Date: {record.date}, Trip #: {record.trip_number}, "
                    f"L: {record.total_liters:.2f}, Cost: ₱{record.cost:.2f}"
                )