import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from fuel.models import Driver, FuelConsumption

class Command(BaseCommand):
    help = 'Populate database with sample fuel consumption data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to generate data for (default: 30)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing FuelConsumption records...')
            FuelConsumption.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing records'))
        
        # Create sample drivers
        drivers_data = [
            ("Antonio Tenebro", "Ambulance L300"),
            ("Grace Zaldy Matos", "Ambulance L300"),
            ("Julchan Mamac", "Ambulance L300"),
            ("Humphrey Daryl Ginggo", "Ambulance Province"),
            ("Jeweriel Sulatorio", "Ambulance Province"),
            ("Crisbanie Jay Paran", "Ambulance DOH"),
            ("Aldren Urot", "Ambulance DOH"),
            ("Mark Joseph Quinalagan", "Backhoe"),
            ("Raymond Hangcan", "Dumptruck"),
        ]
        
        drivers = []
        for name, vehicle in drivers_data:
            driver, created = Driver.objects.get_or_create(
                name=name,
                defaults={'vehicle': vehicle}
            )
            if not created and driver.vehicle != vehicle:
                driver.vehicle = vehicle
                driver.save()
            drivers.append(driver)
        
        # Fixed price per liter
        PRICE_PER_LITER = 62.00
        
        # Destination-based fuel budget (in pesos)
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
        
        # Purpose choices
        purposes = [
            'Transport Patient',
            'landslide sinonok',
            'landslide bag-ong kauswagan',
            'landslide macasing',
            'mahayag medicare',
        ]
        
        # Track trip numbers for each driver and date
        trip_counter = {}
        
        # Generate data for specified number of days
        start_date = date.today() - timedelta(days=options['days'])
        reference_number = 1
        
        for day in range(options['days']):
            current_date = start_date + timedelta(days=day)
            
            # Create 2-5 records per day
            records_per_day = random.randint(2, 5)
            
            for _ in range(records_per_day):
                # Select a random driver
                driver = random.choice(drivers)
                
                # Get or initialize trip number for this driver and date
                key = (driver.id, current_date)
                trip_number = trip_counter.get(key, 1)
                trip_counter[key] = trip_number + 1
                
                # Determine vehicle type and set appropriate data
                if driver.vehicle.startswith('Ambulance'):
                    # Ambulance data
                    destination, budget = random.choice(ambulance_destinations)
                    purpose = random.choice(['Transport Patient', 'mahayag medicare'] if destination == 'mahayag' else ['Transport Patient'])
                    total_liters = budget / PRICE_PER_LITER
                    cost = budget
                    
                    # Special handling for mahayag
                    if destination == 'mahayag':
                        if driver.vehicle != 'Ambulance DOH':
                            # Skip if not DOH ambulance
                            continue
                elif driver.vehicle in ['Backhoe', 'Dumptruck']:
                    # Heavy equipment data
                    destination = 'local'
                    purpose = random.choice(purposes[1:])  # Use special purposes for heavy equipment
                    total_liters = 400.0  # Fixed 400L for heavy equipment
                    cost = total_liters * PRICE_PER_LITER
                else:
                    # Default case
                    destination = 'local'
                    purpose = 'Transport Patient'
                    total_liters = random.uniform(10.0, 50.0)
                    cost = total_liters * PRICE_PER_LITER
                
                # Create passenger name for ambulance trips
                passenger_name = None
                if driver.vehicle.startswith('Ambulance'):
                    passenger_names = [
                        "John Doe", "Jane Smith", "Robert Johnson", "Emily Davis",
                        "Michael Wilson", "Sarah Brown", "David Taylor", "Lisa Miller"
                    ]
                    passenger_name = random.choice(passenger_names)
                
                try:
                    # Create FuelConsumption record
                    FuelConsumption.objects.create(
                        driver=driver,
                        reference_number=reference_number,
                        date=current_date,
                        trip_number=trip_number,
                        number_of_trips=1,
                        purpose=purpose,
                        destination=destination,
                        total_liters=round(total_liters, 2),
                        cost=round(cost, 2),
                        vehicle=driver.vehicle,
                        passenger_name=passenger_name
                    )
                    reference_number += 1
                    
                except ValidationError as e:
                    self.stdout.write(self.style.WARNING(f"Validation error: {e.messages}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating record: {str(e)}"))
        
        # Print summary
        count = FuelConsumption.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated database with {count} FuelConsumption records.')
        )