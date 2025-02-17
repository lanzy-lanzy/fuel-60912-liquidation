import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from fuel.models import Driver, FuelConsumption

class Command(BaseCommand):
    help = 'Simulate fuel consumption with separate gas slips for multiple trips per day using a fixed price of ₱56.50 per liter'

    def handle(self, *args, **kwargs):
        # Set up driver shifts.
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

        # Fixed price per liter.
        PRICE_PER_LITER = 56.50

        # Allocation constants
        TOTAL_BUDGET = 423731.92
        TOTAL_LITERS = TOTAL_BUDGET / PRICE_PER_LITER

        # Allowed random trip cost options.
        trip_cost_options = [1000, 1200, 1500]

        # Simulation period: October 8, 2024 to December 31, 2024.
        start_date = date(2024, 10, 8)
        end_date = date(2024, 12, 31)
        num_days = (end_date - start_date).days + 1

        remaining_fuel = TOTAL_LITERS

        # Dictionary to track trip_number for each (driver.id, date)
        trip_numbers = {}

        for n in range(num_days):
            current_date = start_date + timedelta(n)
            # Optionally skip a specific date if needed (e.g., December 27, 2024)
            if current_date == date(2024, 12, 27):
                continue

            shift_day = n % 4  # For driver shift rotation

            for vehicle, driver_pair in drivers_by_vehicle.items():
                active_driver = driver_pair[0] if shift_day < 2 else driver_pair[1]
                # Two trips on Sundays; one trip on other days.
                trips_today = random.randint(2, 3) if current_date.weekday() == 6 else random.randint(1, 2)

                for _ in range(trips_today):
                    if remaining_fuel <= 0:
                        break

                    selected_cost = random.choice(trip_cost_options)
                    required_liters = selected_cost / PRICE_PER_LITER

                    if remaining_fuel >= required_liters:
                        trip_liters = required_liters
                        trip_cost = selected_cost
                    else:
                        trip_liters = remaining_fuel
                        trip_cost = trip_liters * PRICE_PER_LITER

                    # Determine unique trip number using our in‐memory dictionary.
                    key = (active_driver.id, current_date)
                    trip_numbers[key] = trip_numbers.get(key, 0) + 1
                    trip_number = trip_numbers[key]
                    FuelConsumption.objects.create(
                          driver=active_driver,
                          date=current_date,
                          trip_number=trip_number,
                          number_of_trips=1,
                          purpose="Transport Patient",
                          total_liters=trip_liters,
                          cost=trip_cost,
                          vehicle=active_driver.vehicle  # Add this line to include the vehicle
                    )
                    remaining_fuel -= trip_liters
                if remaining_fuel <= 0:
                    break
            if remaining_fuel <= 0:
                break

        self.stdout.write(
            self.style.SUCCESS(
                f'Fuel consumption simulation completed for October 8, 2024 to December 31, 2024.\n'
                f'Remaining fuel: {remaining_fuel:.2f}L\n'
                f'Remaining budget: ₱{remaining_fuel * PRICE_PER_LITER:.2f}'
            )
        )