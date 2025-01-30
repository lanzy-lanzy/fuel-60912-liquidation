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

        # Distribute consumption among drivers
        for single_date in (start_date + timedelta(n) for n in range(num_days)):
            for driver in drivers:
                # Randomize the number of trips
                number_of_trips = random.randint(1, 2)

                # Calculate total liters ensuring it does not exceed 25 liters per trip
                total_liters = sum(round(random.uniform(15, 25), 2) for _ in range(number_of_trips))
                cost = total_liters * 56.50

                # Adjust total liters if cost exceeds 1500
                if cost > 1500:
                    total_liters = 1500 / 56.50
                    cost = 1500

                # Create a FuelConsumption entry
                FuelConsumption.objects.create(
                    driver=driver,
                    date=single_date,
                    number_of_trips=number_of_trips,
                    purpose="Transport Patient",
                    total_liters=total_liters,
                    cost=cost
                )
        self.stdout.write(self.style.SUCCESS('Successfully simulated fuel consumption'))
