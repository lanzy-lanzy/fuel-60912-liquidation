import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import models
from fuel.models import Driver, FuelConsumption

class Command(BaseCommand):
    help = 'Consume exactly all fuel with the 311,062.35 budget at ₱62.00 per liter'

    def handle(self, *args, **kwargs):
        # Clear all existing FuelConsumption records to avoid unique constraint errors
        FuelConsumption.objects.all().delete()
        
        # Set up driver shifts
        driver_shifts = {
            "Ambulance L300": [
                ("Antonio Tenebro", "Ambulance L300"),
                ("Grace Zaldy Matos", "Ambulance L300"),
                ("Julchan Mamac", "Ambulance L300")
            ],
            "Ambulance Province": [
                ("Humphrey Daryl Ginggo", "Ambulance Province"),
                ("Jeweriel Sulatorio", "Ambulance Province")
            ],
            "Ambulance DOH": [
                ("Crisbanie Jay Paran", "Ambulance DOH"),
                ("Aldren Urot", "Ambulance DOH")
            ],
            "Backhoe": [
                ("Mark Joseph Quinalagan", "Backhoe"),
            ],
            "Dumptruck": [
                ("Raymond Hangcan", "Dumptruck"),
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

        # Fixed price per liter
        PRICE_PER_LITER = 62.00

        # Allocation constants
        TOTAL_BUDGET = 311062.35  # Updated budget
        TOTAL_LITERS = TOTAL_BUDGET / PRICE_PER_LITER  # 5017.135 liters

        # Destination-based fuel budget (in pesos) - for ambulances only
        ambulance_destinations = [
            ('dipolog', 2500),
            ('cagayan', 5000),
            ('margosatubig', 2000),
            ('pagadian_city', 1000),
            ('ozamiz_city', 1500),
            ('zamboanga_city', 5000),
            ('ipil', 3500),
            ('sindangan', 1500),
            ('molave_blancia_hospital', 800),
        ]

        # Special mahayag budget utilization (not a regular destination)
        MAHAYAG_BUDGET_UTILIZATION = 900  # Available for special budget utilization (less than ₱1,000)

        # Create a dictionary for easy lookup
        ambulance_destinations_dict = dict(ambulance_destinations)

        # Simulation period: April 1, 2025 to June 30, 2025
        start_date = date(2025, 4, 1)
        end_date = date(2025, 6, 30)
        num_days = (end_date - start_date).days + 1

        remaining_fuel = TOTAL_LITERS
        remaining_budget = TOTAL_BUDGET

        # Dictionary to track trip_number for each (driver.id, date)
        trip_numbers = {}

        # Reference number counter
        reference_number = 1
        
        # Track total fuel consumed
        total_fuel_consumed = 0
        
        # Track if we've used all special heavy equipment purposes
        special_purposes_used = 0

        # Pre-select four unique dates for heavy equipment special purposes, spread out over the simulation period
        special_purposes = [
            'landslide sinonok',
            'landslide bag-ong kauswagan',
            'landslide macasing',
            'mahayag medicare',
        ]
        special_dates = []
        if num_days >= 4:
            step = num_days // 4
            for i in range(4):
                special_dates.append(start_date + timedelta(i * step))
        else:
            # fallback: just use the first 4 days
            for i in range(4):
                special_dates.append(start_date + timedelta(i))
        special_purpose_date_map = dict(zip(special_dates, special_purposes))

        # Prepare ambulance driver rotation per vehicle
        ambulance_driver_rotations = {}
        for vehicle, driver_list in drivers_by_vehicle.items():
            if vehicle.startswith('Ambulance'):
                ambulance_driver_rotations[vehicle] = {
                    'drivers': driver_list,
                    'index': 0
                }

        # Main simulation loop - continue until we've used most fuel or reached reasonable date limit
        current_date = start_date
        day_counter = 0
        max_days = 180  # Limit to about 6 months to prevent infinite loops

        while remaining_fuel > 0.01 and day_counter < max_days:  # 0.01L threshold - stop when we have minimal amount left
            if day_counter > 0:
                current_date += timedelta(days=1)
                
            # Process each vehicle type
            for vehicle, driver_list in drivers_by_vehicle.items():
                # Skip processing if we're out of fuel
                if remaining_fuel < 0.001:
                    break
                    
                # For ambulances, rotate drivers
                if vehicle.startswith('Ambulance'):
                    rotation = ambulance_driver_rotations[vehicle]
                    active_driver = rotation['drivers'][rotation['index']]
                    rotation['index'] = (rotation['index'] + 1) % len(rotation['drivers'])
                    
                    # Only 1 trip per driver per day
                    trips_today = 1
                    
                    for _ in range(trips_today):
                        # Check if we have enough fuel for at least one trip
                        if remaining_fuel < 10:  # Minimum fuel needed for a short trip
                            break
                            
                        # Get or initialize trip number for this driver and date
                        key = (active_driver.id, current_date)
                        trip_number = trip_numbers.get(key, 1)
                        
                        # Select purpose and destination for this trip
                        selected_purpose = 'Transport Patient'  # Default purpose for ambulances
                        
                        # Filter destinations that fit in remaining fuel and budget
                        possible_destinations = []
                        for dest, cost in ambulance_destinations:
                            required_liters = cost / PRICE_PER_LITER
                            if required_liters <= remaining_fuel and cost <= remaining_budget:
                                possible_destinations.append((dest, cost))

                        # If we have possible destinations, choose one randomly
                        if possible_destinations:
                            selected_destination, trip_cost = random.choice(possible_destinations)
                            required_liters = trip_cost / PRICE_PER_LITER
                        # If no regular destination fits but we have enough for minimum trip
                        elif remaining_fuel >= 10 and remaining_budget >= 10 * PRICE_PER_LITER:
                            selected_destination = random.choice(ambulance_destinations)[0]  # Choose any destination
                            trip_cost = 10 * PRICE_PER_LITER
                            required_liters = 10
                        else:
                            continue  # Skip this trip if we can't even do the minimum
                            
                        try:
                            # Create fuel consumption record with flag to bypass fuel limit check for final trips
                            fuel_record = FuelConsumption(
                                driver=active_driver,
                                reference_number=reference_number,
                                date=current_date,
                                trip_number=trip_number,
                                number_of_trips=1,
                                purpose=selected_purpose,
                                destination=selected_destination,
                                total_liters=required_liters,
                                cost=trip_cost,
                                vehicle=active_driver.vehicle
                            )
                            # Set attribute to bypass fuel limit check
                            fuel_record._bypass_fuel_limit = True
                            fuel_record.save()
                            remaining_fuel -= required_liters
                            remaining_budget -= trip_cost
                            total_fuel_consumed += required_liters
                            reference_number += 1
                            trip_numbers[key] = trip_number + 1
                            
                        except ValidationError as ve:
                            self.stdout.write(self.style.WARNING(f"Validation error: {ve.messages}"))
                
                # For heavy equipment, only schedule on special dates and if we haven't used all special purposes
                elif vehicle in ["Backhoe", "Dumptruck"] and special_purposes_used < 4:
                    if current_date in special_purpose_date_map:
                        active_driver = driver_list[0]  # Only one driver per heavy equipment
                        
                        # Get or initialize trip number for this driver and date
                        key = (active_driver.id, current_date)
                        trip_number = trip_numbers.get(key, 1)
                        
                        # Use the special purpose for this date
                        selected_purpose = special_purpose_date_map[current_date]
                        selected_destination = 'local'  # Heavy equipment only does local trips
                        
                        # Calculate fuel needed (400L per trip for heavy equipment)
                        required_liters = 400.0
                        trip_cost = required_liters * PRICE_PER_LITER
                        
                        # Only proceed if we have enough fuel and budget for this heavy equipment trip
                        if required_liters <= remaining_fuel and trip_cost <= remaining_budget:
                            try:
                                # Create fuel consumption record with flag to bypass fuel limit check for final trips
                                fuel_record = FuelConsumption(
                                    driver=active_driver,
                                    reference_number=reference_number,
                                    date=current_date,
                                    trip_number=trip_number,
                                    number_of_trips=1,
                                    purpose=selected_purpose,
                                    destination=selected_destination,
                                    total_liters=required_liters,
                                    cost=trip_cost,
                                    vehicle=active_driver.vehicle
                                )
                                # Set attribute to bypass fuel limit check
                                fuel_record._bypass_fuel_limit = True
                                fuel_record.save()
                                remaining_fuel -= required_liters
                                remaining_budget -= trip_cost
                                total_fuel_consumed += required_liters
                                reference_number += 1
                                trip_numbers[key] = trip_number + 1
                                special_purposes_used += 1
                                
                            except ValidationError as ve:
                                self.stdout.write(self.style.WARNING(f"Validation error: {ve.messages}"))
            
            day_counter += 1
            
            # If we've reached the end date but still have significant fuel, continue a bit more
            if current_date >= end_date and remaining_fuel > 10:
                self.stdout.write(self.style.WARNING(f"Extended simulation beyond {end_date} to utilize remaining fuel"))
                end_date += timedelta(days=1)

        # Use remaining fuel with Mahayag trips as last resort to consume exactly all fuel
        if remaining_fuel > 0.001:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Consuming remaining fuel for Mahayag trips: ₱{remaining_budget:,.2f} ({remaining_fuel:.2f}L)')
            )
            
            # Add final trips using Ambulance DOH for mahayag until fuel is exhausted
            try:
                # Get the last reference number
                last_ref = FuelConsumption.objects.order_by('-reference_number').first()
                next_ref = (last_ref.reference_number + 1) if last_ref else 1

                # Get an Ambulance DOH driver
                driver = Driver.objects.filter(vehicle='Ambulance DOH').first()
                if not driver:
                    # Fallback to any ambulance driver
                    driver = Driver.objects.filter(vehicle__icontains='Ambulance').first()
                if not driver:
                    raise Exception("No ambulance drivers found in the database")

                # Calculate how many Mahayag trips we can make with remaining fuel
                # Each Mahayag trip uses MAHAYAG_BUDGET_UTILIZATION worth of fuel
                MAHAYAG_LITERS = MAHAYAG_BUDGET_UTILIZATION / PRICE_PER_LITER
                
                # Make as many complete Mahayag trips as possible
                complete_trips = int(remaining_fuel // MAHAYAG_LITERS)
                
                # Get the highest trip number for this driver on this date
                max_trip_number = FuelConsumption.objects.filter(
                    driver=driver, date=current_date
                ).aggregate(models.Max('trip_number'))['trip_number__max'] or 0
                
                for i in range(complete_trips):
                    # Create fuel consumption record with flag to bypass fuel limit check for final trips
                    fuel_record = FuelConsumption(
                        date=current_date,
                        driver=driver,
                        vehicle='Ambulance DOH',
                        destination='mahayag',
                        purpose='Transport Patient',
                        total_liters=MAHAYAG_LITERS,
                        cost=MAHAYAG_BUDGET_UTILIZATION,
                        reference_number=next_ref + i,
                        trip_number=max_trip_number + i + 1
                    )
                    # Set attribute to bypass fuel limit check
                    fuel_record._bypass_fuel_limit = True
                    fuel_record.save()
                    remaining_fuel -= MAHAYAG_LITERS
                    remaining_budget -= MAHAYAG_BUDGET_UTILIZATION
                    total_fuel_consumed += MAHAYAG_LITERS
                    
                # If there's any remaining fuel that's less than a full Mahayag trip, use it
                if remaining_fuel > 0.001:
                    # Calculate exact liters and cost to consume all remaining fuel
                    exact_liters = round(remaining_fuel, 2)
                    exact_cost = round(remaining_fuel * PRICE_PER_LITER, 2)
                    
                    # Create fuel consumption record with flag to bypass fuel limit check for final trips
                    fuel_record = FuelConsumption(
                        date=current_date,
                        driver=driver,
                        vehicle='Ambulance DOH',
                        destination='mahayag',
                        purpose='Transport Patient',
                        total_liters=exact_liters,
                        cost=exact_cost,
                        reference_number=next_ref + complete_trips,
                        trip_number=max_trip_number + complete_trips + 1
                    )
                    # Set attribute to bypass fuel limit check
                    fuel_record._bypass_fuel_limit = True
                    fuel_record.save()
                    total_fuel_consumed += remaining_fuel
                    remaining_fuel = 0
                    remaining_budget = 0
                
                if complete_trips > 0 or remaining_fuel <= 0.001:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Added {complete_trips} complete Mahayag trip(s) and final partial trip for remaining fuel')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Budget fully utilized with no remaining fuel')
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to add Mahayag trips: {str(e)}')
                )

        # Print summary
        count = FuelConsumption.objects.count()
        total_cost = total_fuel_consumed * PRICE_PER_LITER
        utilization = (total_fuel_consumed / TOTAL_LITERS) * 100
        
        self.stdout.write(
            self.style.SUCCESS(f'Simulation completed on {current_date}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created {count} FuelConsumption records.')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total fuel consumed: {total_fuel_consumed:.2f}L')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cost: ₱{total_cost:,.2f}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Budget utilization: {(total_cost / TOTAL_BUDGET) * 100:.2f}%')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Remaining fuel: {remaining_fuel:.2f}L (₱{remaining_fuel * PRICE_PER_LITER:,.2f})')
        )
        
        # Verify exact consumption
        if abs(remaining_fuel) < 0.001:
            self.stdout.write(
                self.style.SUCCESS('✅ All fuel has been consumed exactly!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Small amount of fuel remaining: {remaining_fuel:.2f}L')
            )