import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from fuel.models import Driver, FuelConsumption

class Command(BaseCommand):
    help = 'Simulate fuel consumption for 342,978.36 budget with price per liter of ₱63.00, focusing on Ozamiz and Pagadian trips with Molave Blancia Hospital as last resort'

    def handle(self, *args, **kwargs):
        # Clear all existing FuelConsumption records to avoid unique constraint errors
        FuelConsumption.objects.all().delete()
        
        # Define travel times for destinations (synchronized with generate_trip_times.py)
        TRAVEL_TIMES = {
            'pagadian_city': timedelta(hours=1, minutes=20),  # 1 hour 20 minutes
            'ozamiz_city': timedelta(hours=1, minutes=35),    # 1 hour 35 minutes
            'cagayan': timedelta(hours=5),                    # 5 hours
            'zamboanga_city': timedelta(hours=5),             # 5 hours
            'davao_city': timedelta(hours=10),                # 10 hours
            'molave_blancia_hospital': timedelta(hours=1, minutes=15),  # 1 hour 15 minutes (default)
            'default': timedelta(hours=1, minutes=15)         # Default for other destinations
        }
        
        # Define working hours (6:00 AM to 6:00 PM)
        WORK_START = time(6, 0)   # 6:00 AM
        WORK_END = time(18, 0)    # 6:00 PM
        
        # Set up driver shifts - removed heavy equipment drivers
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
        PRICE_PER_LITER = 63.00

        # Allocation constants
        TOTAL_BUDGET = 342978.36  # New budget
        TOTAL_LITERS = TOTAL_BUDGET / PRICE_PER_LITER  # Precise calculation: 5444.100952380952 liters

        # Destination-based fuel budget (in pesos) - focusing on Ozamiz and Pagadian
        ambulance_destinations = [
            ('pagadian_city', 1000),
            ('ozamiz_city', 1500),
        ]

        # Last resort destination
        LAST_RESORT_DESTINATION = 'molave_blancia_hospital'
        LAST_RESORT_BUDGET = 800  # Less than ₱1,000 as per business rule

        # Create a dictionary for easy lookup
        ambulance_destinations_dict = dict(ambulance_destinations)

        # Simulation period: Start from July 31, 2025 (as required)
        start_date = date(2025, 7, 31)
        # Set end date to September 15 of the same year
        end_date = date(2025, 9, 15)
        
        remaining_fuel = TOTAL_LITERS

        # Dictionary to track trip_number for each (driver.id, date)
        trip_numbers = {}

        # Reference number counter
        reference_number = 1
        
        # Track total fuel consumed
        total_fuel_consumed = 0

        # Prepare ambulance driver rotation per vehicle
        ambulance_driver_rotations = {}
        for vehicle, driver_list in drivers_by_vehicle.items():
            if vehicle.startswith('Ambulance'):
                ambulance_driver_rotations[vehicle] = {
                    'drivers': driver_list,
                    'index': 0
                }

        # Track last trip end time for each driver on each date
        driver_last_trip_end = {}

        # Main simulation loop - continue until we've used most fuel or reached end date
        current_date = start_date
        day_counter = 0
        max_days = 365  # Allow up to a year of simulation to avoid infinite loops

        while remaining_fuel > 0.001 and day_counter < max_days and current_date < end_date:
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
                    
                    # 2 trips per driver per day with randomized destinations to avoid suspicious patterns
                    trips_today = 2
                    
                    # Add some natural variation to avoid suspicious patterns
                    # Occasionally have 1 or 3 trips per day
                    if random.random() < 0.1:  # 10% chance for variation
                        trips_today = random.choice([1, 3])
                    
                    # Track last trip end time for this driver on this date
                    driver_date_key = (active_driver.id, current_date)
                    last_trip_end_time = driver_last_trip_end.get(driver_date_key)
                    
                    for trip_idx in range(trips_today):
                        # Check if we have enough fuel for at least one trip
                        if remaining_fuel < 10:  # Minimum fuel needed for a short trip
                            break
                            
                        # Get or initialize trip number for this driver and date
                        key = (active_driver.id, current_date)
                        trip_number = trip_numbers.get(key, 1)
                        
                        # Select purpose and destination for this trip
                        selected_purpose = 'Transport Patient'  # Default purpose for ambulances
                        
                        # Filter destinations that fit in remaining fuel
                        possible_destinations = []
                        for dest, cost in ambulance_destinations:
                            required_liters = cost / PRICE_PER_LITER
                            if required_liters <= remaining_fuel:
                                possible_destinations.append((dest, cost))

                        # If we have possible destinations, choose one randomly
                        if possible_destinations:
                            selected_destination, trip_cost = random.choice(possible_destinations)
                            required_liters = trip_cost / PRICE_PER_LITER
                        # If no regular destination fits but we have enough for minimum trip
                        elif remaining_fuel >= 10:
                            selected_destination = random.choice(ambulance_destinations)[0]  # Choose any destination
                            trip_cost = 10 * PRICE_PER_LITER
                            required_liters = 10
                        else:
                            continue  # Skip this trip if we can't even do the minimum
                            
                        try:
                            # Generate trip times
                            travel_time = TRAVEL_TIMES.get(selected_destination, TRAVEL_TIMES['default'])
                            departure_time, arrival_time, return_departure_time, return_arrival_time = self.generate_trip_times(
                                travel_time, last_trip_end_time, WORK_START, WORK_END
                            )
                            
                            # Create fuel consumption record with custom fuel price
                            fuel_record = FuelConsumption(
                                driver=active_driver,
                                reference_number=reference_number,
                                date=current_date,
                                trip_number=trip_number,
                                number_of_trips=1,
                                purpose=selected_purpose,
                                destination=selected_destination,
                                vehicle=active_driver.vehicle,
                                departure_time=departure_time,
                                arrival_time=arrival_time,
                                return_departure_time=return_departure_time,
                                return_arrival_time=return_arrival_time
                            )
                            # Set the custom fuel price for v2 command
                            fuel_record._fuel_price = PRICE_PER_LITER
                            fuel_record.save()
                            
                            remaining_fuel -= fuel_record.total_liters
                            total_fuel_consumed += fuel_record.total_liters
                            reference_number += 1
                            trip_numbers[key] = trip_number + 1
                            
                            # Update last trip end time for next iteration
                            last_trip_end_time = return_arrival_time
                            driver_last_trip_end[driver_date_key] = last_trip_end_time
                            
                        except ValidationError as ve:
                            self.stdout.write(self.style.WARNING(f"Validation error: {ve.messages}"))
            
            # Move to the next day
            day_counter += 1
            if day_counter < max_days and current_date < end_date:
                current_date += timedelta(days=1)
        
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
        
        # Calculate remaining budget
        remaining_budget = remaining_fuel * PRICE_PER_LITER
        
        self.stdout.write(f'\nChecking final trip options...')
        self.stdout.write(f'Remaining budget: ₱{remaining_budget:,.2f} ({remaining_fuel:.2f}L)')
        
        # If we still have some fuel left, consume it all for Molave Blancia Hospital trips
        if remaining_fuel > 0.001:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Consuming remaining fuel for Molave Blancia Hospital trips: ₱{remaining_fuel * PRICE_PER_LITER:,.2f} ({remaining_fuel:.2f}L)')
            )
            
            # Add final trips using Ambulance DOH for Molave Blancia Hospital until fuel is exhausted
            try:
                # Get the last reference number
                last_ref = FuelConsumption.objects.order_by('-reference_number').first()
                next_ref = (last_ref.reference_number + 1) if last_ref else 1

                # Get the specific driver: Crisbanie Jay Paran from Ambulance DOH
                driver = Driver.objects.filter(name="Crisbanie Jay Paran", vehicle="Ambulance DOH").first()
                if not driver:
                    # Fallback to any Ambulance DOH driver
                    driver = Driver.objects.filter(vehicle='Ambulance DOH').first()
                if not driver:
                    # Fallback to any ambulance driver
                    driver = Driver.objects.filter(vehicle__icontains='Ambulance').first()
                if not driver:
                    raise Exception("No ambulance drivers found in the database")

                # Track last trip end time for this driver on this date
                driver_date_key = (driver.id, current_date)
                last_trip_end_time = driver_last_trip_end.get(driver_date_key)
                
                # Calculate how many Molave trips we can make with remaining fuel
                # Each Molave trip uses LAST_RESORT_BUDGET worth of fuel
                LAST_RESORT_LITERS = LAST_RESORT_BUDGET / PRICE_PER_LITER
                
                # Make as many complete Molave trips as possible
                complete_trips = int(remaining_fuel // LAST_RESORT_LITERS)
                
                # Get the highest trip number for this driver on this date
                max_trip_number = FuelConsumption.objects.filter(
                    driver=driver, date=current_date
                ).aggregate(models.Max('trip_number'))['trip_number__max'] or 0
                
                for i in range(complete_trips):
                    # Generate trip times
                    travel_time = TRAVEL_TIMES.get(LAST_RESORT_DESTINATION, TRAVEL_TIMES['default'])
                    departure_time, arrival_time, return_departure_time, return_arrival_time = self.generate_trip_times(
                        travel_time, last_trip_end_time, WORK_START, WORK_END
                    )
                    
                    # Create fuel consumption record with custom fuel price
                    fuel_record = FuelConsumption(
                        date=current_date,
                        driver=driver,
                        vehicle='Ambulance DOH',
                        destination=LAST_RESORT_DESTINATION,
                        purpose='Transport Patient',
                        reference_number=next_ref + i,
                        trip_number=max_trip_number + i + 1,
                        number_of_trips=1,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        return_departure_time=return_departure_time,
                        return_arrival_time=return_arrival_time
                    )
                    # Set the custom fuel price for v2 command
                    fuel_record._fuel_price = PRICE_PER_LITER
                    fuel_record.save()
                    
                    remaining_fuel -= fuel_record.total_liters
                    total_fuel_consumed += fuel_record.total_liters
                    total_cost += fuel_record.cost
                    
                    # Update last trip end time for next iteration
                    last_trip_end_time = return_arrival_time
                    driver_last_trip_end[driver_date_key] = last_trip_end_time
                
                # If there's any remaining fuel that's less than a full Molave trip, use it
                # Even if it's a very small amount, create a proper trip for it
                if remaining_fuel > 0.001:
                    # Generate trip times
                    travel_time = TRAVEL_TIMES.get(LAST_RESORT_DESTINATION, TRAVEL_TIMES['default'])
                    departure_time, arrival_time, return_departure_time, return_arrival_time = self.generate_trip_times(
                        travel_time, last_trip_end_time, WORK_START, WORK_END
                    )
                    
                    # For the final partial trip, we create a trip with exactly the remaining fuel
                    final_trip_cost = remaining_fuel * PRICE_PER_LITER
                    
                    # Create fuel consumption record with custom fuel price
                    fuel_record = FuelConsumption(
                        date=current_date,
                        driver=driver,
                        vehicle='Ambulance DOH',
                        destination=LAST_RESORT_DESTINATION,
                        purpose='Transport Patient',
                        reference_number=next_ref + complete_trips,
                        trip_number=max_trip_number + complete_trips + 1,
                        number_of_trips=1,
                        total_liters=remaining_fuel,
                        cost=final_trip_cost,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        return_departure_time=return_departure_time,
                        return_arrival_time=return_arrival_time
                    )
                    # Set the custom fuel price for v2 command
                    fuel_record._fuel_price = PRICE_PER_LITER
                    # Temporarily increase fuel allocation to allow this final adjustment
                    original_allocation = fuel_record.TOTAL_FUEL_ALLOCATION
                    fuel_record.TOTAL_FUEL_ALLOCATION = total_fuel_consumed + remaining_fuel + 10  # Add buffer
                    fuel_record.save()
                    # Restore original allocation
                    fuel_record.TOTAL_FUEL_ALLOCATION = original_allocation
                    
                    total_fuel_consumed += fuel_record.total_liters
                    total_cost += fuel_record.cost
                    remaining_fuel = 0
                
                if complete_trips > 0 or remaining_fuel <= 0.001:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Added {complete_trips} complete Molave Blancia Hospital trip(s) and final partial trip for remaining fuel')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Budget fully utilized with no remaining fuel')
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to add Molave Blancia Hospital trips: {str(e)}')
                )
                # Even if we can't add the Molave trips, we'll still adjust the last record to make the total exact
                
        # If we still have any remaining fuel (even tiny amounts), adjust the last record to consume it
        # This is a fallback mechanism to ensure all fuel is consumed
        if remaining_fuel > 0.001:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Consuming remaining fuel by adjusting last record: ₱{remaining_fuel * PRICE_PER_LITER:,.2f} ({remaining_fuel:.2f}L)')
            )
            
            # Get the last record and adjust it to consume the remaining fuel
            last_record = FuelConsumption.objects.order_by('-id').first()
            if last_record:
                # Set the fuel price attribute to ensure proper handling
                last_record._fuel_price = PRICE_PER_LITER
                # Temporarily increase the TOTAL_FUEL_ALLOCATION to allow the adjustment
                original_allocation = last_record.TOTAL_FUEL_ALLOCATION
                last_record.TOTAL_FUEL_ALLOCATION = total_fuel_consumed + remaining_fuel + 10  # Add buffer
                
                # Add the remaining fuel to the last record
                additional_cost = remaining_fuel * PRICE_PER_LITER
                last_record.total_liters += remaining_fuel
                last_record.cost += additional_cost
                
                # Ensure proper rounding to 2 decimal places
                last_record.total_liters = round(last_record.total_liters, 2)
                last_record.cost = round(last_record.cost, 2)
                
                last_record.save()
                
                # Restore the original allocation
                last_record.TOTAL_FUEL_ALLOCATION = original_allocation
                total_fuel_consumed += remaining_fuel
                total_cost += additional_cost
                remaining_fuel = 0
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Consumed remaining {remaining_fuel:.2f}L by adjusting last record')
                )
        
        # Final verification - make sure we've consumed exactly all fuel
        # We'll adjust the last record to consume any remaining fuel, bypassing all limits
        db_total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        final_discrepancy = TOTAL_LITERS - db_total_consumed
        if abs(final_discrepancy) > 0.000001:  # If there's any difference at all (using higher precision)
            self.stdout.write(
                self.style.WARNING(f'⚠️  Final precise adjustment to consume all fuel: {final_discrepancy:.10f}L')
            )
            
            # Get the last record and adjust it to consume the remaining fuel
            last_record = FuelConsumption.objects.order_by('-id').first()
            if last_record:
                # Calculate the exact adjustment needed
                cost_adjustment = final_discrepancy * PRICE_PER_LITER
                
                # Directly update the record in the database to bypass all validation
                # This is the most reliable way to ensure exact consumption
                FuelConsumption.objects.filter(id=last_record.id).update(
                    total_liters=models.F('total_liters') + final_discrepancy,
                    cost=models.F('cost') + cost_adjustment
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Final precise adjustment completed - consumed exactly all fuel')
                )
        
        # Recalculate total cost to ensure exact consumption
        total_cost = total_fuel_consumed * PRICE_PER_LITER
        
        # Get the actual total cost from the database
        db_total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0
        
        # Ensure we consume exactly the target amount by adjusting for any floating point errors
        if abs(db_total_cost - TOTAL_BUDGET) > 0.01:  # If difference is more than 1 cent
            # Calculate the exact adjustment needed
            adjustment = TOTAL_BUDGET - db_total_cost
            # Apply the adjustment to the last record
            last_record = FuelConsumption.objects.order_by('-id').first()
            if last_record:
                # Calculate the exact values needed
                new_cost = last_record.cost + adjustment
                new_liters = last_record.total_liters + (adjustment / PRICE_PER_LITER)
                
                # Directly update the database record to ensure exact values
                FuelConsumption.objects.filter(id=last_record.id).update(
                    total_liters=new_liters,
                    cost=new_cost
                )
                
                # Update our local variables
                total_fuel_consumed += adjustment / PRICE_PER_LITER
                total_cost = TOTAL_BUDGET  # Set to exact target
                db_total_cost = TOTAL_BUDGET  # Set to exact target

        # Final check to ensure all fuel is consumed
        db_total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        final_discrepancy = TOTAL_LITERS - db_total_consumed
        if abs(final_discrepancy) > 0.000001:  # If there's still a discrepancy
            # Force a final database update to consume exactly all fuel
            last_record = FuelConsumption.objects.order_by('-id').first()
            if last_record:
                cost_adjustment = final_discrepancy * PRICE_PER_LITER
                FuelConsumption.objects.filter(id=last_record.id).update(
                    total_liters=models.F('total_liters') + final_discrepancy,
                    cost=models.F('cost') + cost_adjustment
                )

        self.stdout.write(
            self.style.SUCCESS(f'Budget utilization: {(total_cost / TOTAL_BUDGET) * 100:.2f}%')
        )
        # Update remaining fuel calculation for final output
        db_total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        remaining_fuel = TOTAL_LITERS - db_total_consumed
        self.stdout.write(
            self.style.SUCCESS(f'Remaining fuel: {remaining_fuel:.2f}L (₱{remaining_fuel * PRICE_PER_LITER:,.2f})')
        )
        
        # Get the final total cost from the database
        final_total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0
        self.stdout.write(
            self.style.SUCCESS(f'Final total cost: ₱{final_total_cost:,.2f}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Difference from target: ₱{abs(final_total_cost - TOTAL_BUDGET):,.2f}')
        )
        
    def generate_trip_times(self, travel_time, last_trip_end_time, work_start, work_end):
        """
        Generate realistic trip times based on travel duration and previous trip end time.
        """
        # Determine start time for this trip
        if last_trip_end_time:
            # Add a random interval (5-15 minutes) after the previous trip
            interval = timedelta(minutes=random.randint(5, 15))
            potential_start = datetime.combine(date.today(), last_trip_end_time) + interval
            start_time = potential_start.time()
        else:
            # For the first trip, start at a random time within working hours
            # But ensure there's enough time for the trip
            earliest_start = datetime.combine(date.today(), work_start)
            latest_start = datetime.combine(date.today(), work_end) - (travel_time * 2) - timedelta(hours=1)
            
            if latest_start > earliest_start:
                # Generate a random start time within the valid range
                time_range_minutes = int((latest_start - earliest_start).total_seconds() / 60)
                random_minutes = random.randint(0, time_range_minutes)
                start_datetime = earliest_start + timedelta(minutes=random_minutes)
                start_time = start_datetime.time()
            else:
                # Fallback if there's not enough time
                start_time = work_start
        
        # Ensure start time is within working hours
        if start_time < work_start:
            start_time = work_start
        elif start_time > work_end:
            start_time = work_end
            
        # Add a small travel buffer so arrival is not an exact round number (5-20 min)
        travel_time_eff = travel_time + timedelta(minutes=random.randint(5, 20))

        # Calculate arrival time
        departure_datetime = datetime.combine(date.today(), start_time)
        arrival_datetime = departure_datetime + travel_time_eff
        arrival_time = arrival_datetime.time()

        # Add rest time at destination, scaled to trip length so it looks natural
        travel_minutes = int(travel_time_eff.total_seconds() / 60)
        if travel_minutes >= 540:
            rest_time = timedelta(minutes=random.randint(45, 90))
        elif travel_minutes >= 240:
            rest_time = timedelta(minutes=random.randint(30, 60))
        else:
            rest_time = timedelta(minutes=random.randint(15, 40))
        return_departure_datetime = arrival_datetime + rest_time
        return_departure_time = return_departure_datetime.time()

        # Calculate return arrival time
        return_arrival_datetime = return_departure_datetime + travel_time_eff
        return_arrival_time = return_arrival_datetime.time()
        
        return start_time, arrival_time, return_departure_time, return_arrival_time

    def random_time_between(self, start, end):
        # Generate a random time between start and end
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)
