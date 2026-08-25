import random
from datetime import datetime, time, timedelta, date
from django.core.management.base import BaseCommand
from fuel.models import FuelConsumption

class Command(BaseCommand):
    help = 'Generate realistic departure and arrival times for fuel consumption records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to generate times for (YYYY-MM-DD), or "all" for all records',
            default='all'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of times even if they already exist',
            default=False
        )

    def handle(self, *args, **options):
        # Define travel times for destinations (synchronized with consume_fuel_v2.py)
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
        
        # Define vehicle processing order to match consume_fuel_v2.py
        VEHICLE_ORDER = ['Ambulance L300', 'Ambulance Province', 'Ambulance DOH']
        
        if options['date'] == 'all':
            records = FuelConsumption.objects.all()
        else:
            records = FuelConsumption.objects.filter(date=options['date'])
            
        # Filter out records that already have times unless force flag is used
        if not options['force']:
            records = records.filter(departure_time__isnull=True)
            
        updated_count = 0
        
        # Group records by date for proper sequencing across all drivers
        records_by_date = {}
        for record in records:
            date_key = record.date
            if date_key not in records_by_date:
                records_by_date[date_key] = []
            records_by_date[date_key].append(record)
            
        # Process records date by date
        for date_key, date_records in records_by_date.items():
            # Create a mapping of vehicle to drivers for this date
            vehicle_driver_map = {}
            for record in date_records:
                vehicle = record.driver.vehicle
                if vehicle not in vehicle_driver_map:
                    vehicle_driver_map[vehicle] = []
                if record.driver not in vehicle_driver_map[vehicle]:
                    vehicle_driver_map[vehicle].append(record.driver)
            
            # Sort drivers within each vehicle by name
            for vehicle in vehicle_driver_map:
                vehicle_driver_map[vehicle].sort(key=lambda d: d.name)
            
            # Sort records by vehicle order, then by driver name, then by trip number
            def sort_key(record):
                try:
                    vehicle_index = VEHICLE_ORDER.index(record.driver.vehicle)
                except ValueError:
                    vehicle_index = len(VEHICLE_ORDER)  # Put unknown vehicles at the end
                driver_index = vehicle_driver_map[record.driver.vehicle].index(record.driver)
                return (vehicle_index, driver_index, record.trip_number)
            
            date_records.sort(key=sort_key)
            
            # Track the end time of the previous trip for each driver
            driver_last_trip_end = {}
            
            for record in date_records:
                # Get the last trip end time for this driver
                driver_key = record.driver.id
                last_trip_end_time = driver_last_trip_end.get(driver_key)
                
                # Check if this is a local area trip
                is_local_trip = record.destination == 'local'
                
                # Get travel time for this destination
                travel_time = TRAVEL_TIMES.get(record.destination, TRAVEL_TIMES['default'])
                
                # Generate times for this trip
                if is_local_trip:
                    # For local trips, set specific times: departure at 8:00 AM and return arrival at 5:00 PM
                    departure_time = time(8, 0)  # 8:00 AM
                    return_arrival_time = time(17, 0)  # 5:00 PM
                    # Set arrival and return departure times to None for local trips
                    arrival_time = None
                    return_departure_time = None
                else:
                    # For non-local trips, generate all times
                    departure_time, arrival_time, return_departure_time, return_arrival_time = self.generate_trip_times(
                        travel_time, last_trip_end_time, WORK_START, WORK_END
                    )
                
                # Update the record with the generated times
                record.departure_time = departure_time
                record.arrival_time = arrival_time
                record.return_departure_time = return_departure_time
                record.return_arrival_time = return_arrival_time
                record.save(update_fields=['departure_time', 'arrival_time', 'return_departure_time', 'return_arrival_time'])
                
                # Update last trip end time for this driver
                driver_last_trip_end[driver_key] = return_arrival_time
                updated_count += 1
                
                if is_local_trip:
                    self.stdout.write(
                        f"Driver: {record.driver.name}, Date: {record.date}, "
                        f"Trip #{record.trip_number} - "
                        f"Depart: {departure_time.strftime('%H:%M')}, "
                        f"Return Arrive: {return_arrival_time.strftime('%H:%M')} (LOCAL TRIP)"
                    )
                else:
                    self.stdout.write(
                        f"Driver: {record.driver.name}, Date: {record.date}, "
                        f"Trip #{record.trip_number} - "
                        f"Depart: {departure_time.strftime('%H:%M')}, "
                        f"Arrive: {arrival_time.strftime('%H:%M')}, "
                        f"Return Depart: {return_departure_time.strftime('%H:%M')}, "
                        f"Return Arrive: {return_arrival_time.strftime('%H:%M')}"
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} records with trip times')
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