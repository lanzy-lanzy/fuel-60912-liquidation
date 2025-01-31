from django.core.management.base import BaseCommand
from fuel.models import Driver, FuelConsumption
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Simulate fuel consumption for drivers with shift rotation'

    def handle(self, *args, **kwargs):
        driver_shifts = {
            "Ambulance L300": [
                ("Julchan Mamac", "Ambulance L300"),
                ("Rey Berjame", "Ambulance L300")
            ],
            "Ambulance Province": [
                ("Humphrey Daryl Ginggo", "Ambulance Province"),
                ("Jeweriel Sulatorio", "Ambulance Province")
            ],
            "Ambulance DOH": [
                ("Crisbanie Jay Paran", "Ambulance DOH"),
                ("Aldren Urot", "Ambulance DOH")
            ]
        }

        drivers_by_vehicle = {}
        for vehicle, driver_list in driver_shifts.items():
            drivers_by_vehicle[vehicle] = []
            for name, vehicle_type in driver_list:
                driver, created = Driver.objects.get_or_create(
                    name=name,
                    defaults={'vehicle': vehicle_type}
                )
                if not created and driver.vehicle != vehicle_type:
                    driver.vehicle = vehicle_type
                    driver.save()
                drivers_by_vehicle[vehicle].append(driver)

        start_date = date(2024, 10, 13)
        end_date = date(2024, 12, 31)
        num_days = (end_date - start_date).days + 1

        remaining_fuel = round(FuelConsumption.TOTAL_FUEL_ALLOCATION, 2)
        working_days = num_days - 1  # Excluding Dec 27
        vehicles_count = len(driver_shifts)

        # Set strict limits for fuel consumption
        min_liters = 15.00
        max_liters = 25.00

        for n in range(num_days):
            current_date = start_date + timedelta(n)
            
            if current_date == date(2024, 12, 27):
                continue

            shift_day = n % 4

            for vehicle, driver_pair in drivers_by_vehicle.items():
                active_driver = driver_pair[0] if shift_day < 2 else driver_pair[1]
                trips_today = 2 if current_date.weekday() == 6 else 1

                # Calculate fuel within strict limits
                daily_liters = round(random.uniform(min_liters, max_liters), 2)

                if remaining_fuel >= daily_liters:
                    cost = round(daily_liters * FuelConsumption.FUEL_PRICE, 2)
                    FuelConsumption.objects.create(
                        driver=active_driver,
                        date=current_date,
                        number_of_trips=trips_today,
                        purpose="Transport Patient",
                        total_liters=daily_liters,
                        cost=cost
                    )
                    remaining_fuel = round(remaining_fuel - daily_liters, 2)

        self.stdout.write(
            self.style.SUCCESS(
                f'Fuel consumption simulation completed. '
                f'Remaining fuel: {remaining_fuel:.2f}L'
            )
        )
