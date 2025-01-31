from django.core.management.base import BaseCommand
from fuel.models import Driver, FuelConsumption
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Simulate fuel consumption for drivers'

    def handle(self, *args, **kwargs):
        # Define the drivers
        driver_names = [
            "Julchan Mamac",
            "Crisbanie Jay Paran",
            "Aldren Urot",
            "Humphrey Daryl Ginggo",
            "Jeweriel Sulatorio",
            "Rey Berjame"
        ]

        # Create drivers if they don't exist
        drivers = []
        for name in driver_names:
            driver, created = Driver.objects.get_or_create(name=name)
            drivers.append(driver)

        # Define the date range
        start_date = date(2024, 10, 13)
        end_date = date(2024, 12, 31)
        num_days = (end_date - start_date).days + 1

        # Define total available fuel
        total_available_fuel = 7499.68  # Example total fuel available

        # Distribute consumption among drivers
        for n in range(num_days):
            single_date = start_date + timedelta(n)

            # Skip December 27, 2024
            if single_date == date(2024, 12, 27):
                continue

            # Determine if today should be a two-trip day
            is_two_trip_day = (single_date.weekday() == 6)  # Sunday as a two-trip day

            for driver in drivers:
                # Determine the number of trips for the day
                trips_today = 2 if is_two_trip_day else 1

                for _ in range(trips_today):
                    # Check if an entry already exists for this driver and date
                    if FuelConsumption.objects.filter(driver=driver, date=single_date).exists():
                        continue  # Skip creating a duplicate entry

                    # Randomly choose a total liters value between 1000 and 1500 for each trip
                    total_liters = random.uniform(1000, 1500)
                    cost = total_liters * 56.50  # Assuming cost per liter is 56.50

                    # Deduct the used fuel from the total available fuel
                    total_available_fuel -= total_liters

                    # Create a FuelConsumption entry for each trip
                    FuelConsumption.objects.create(
                        driver=driver,
                        date=single_date,
                        number_of_trips=1,  # Each entry represents a single trip
                        purpose="Transport Patient",
                        total_liters=total_liters,
                        cost=cost
                    )

        self.stdout.write(self.style.SUCCESS('Successfully simulated fuel consumption'))