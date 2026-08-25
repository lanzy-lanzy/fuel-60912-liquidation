import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from fuel.models import Driver, FuelConsumption

class Command(BaseCommand):
    help = 'Reset database and populate with specific fuel trip data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all existing fuel consumption records'
        )

    def handle(self, *args, **kwargs):
        if not kwargs['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '[WARN] This command will DELETE all existing FuelConsumption records!\n'
                    'To proceed, run: python manage.py reset_custom_fuel_data --confirm'
                )
            )
            return

        # Clear all existing FuelConsumption records
        old_count = FuelConsumption.objects.count()
        FuelConsumption.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'[OK] Cleared {old_count} existing FuelConsumption records')
        )

        # -- Budget & Fuel Config --
        TOTAL_BUDGET = 60912.00
        PRICE_PER_LITER = 126.90
        # 60912.00 / 126.90 = 480.00 liters exactly
        TOTAL_LITERS_TARGET = round(TOTAL_BUDGET / PRICE_PER_LITER, 2)

        self.stdout.write(f'\n  Budget:       P{TOTAL_BUDGET:,.2f}')
        self.stdout.write(f'  Price/Liter:  P{PRICE_PER_LITER:.2f}')
        self.stdout.write(f'  Target Liters: {TOTAL_LITERS_TARGET:.2f}L')

        # -- Travel Times --
        TRAVEL_TIMES = {
            'pagadian_city': timedelta(hours=1, minutes=10),
            'ozamiz_city': timedelta(hours=1, minutes=20),
        }

        # -- Driver Setup --
        driver_configs = [
            ("Crisbanie Jay Paran", "Ambulance PTV"),
            ("Humphrey Daryl Ginggo", "Ambulance Province"),
            ("Grace Zaldy Matos", "Ambulance DOH"),
            ("Jeweriel Sulatorio", "Ambulance Province"),
            ("Aldren Urot", "Ambulance PTV"),
        ]

        drivers = {}
        for name, vehicle_type in driver_configs:
            driver, created = Driver.objects.get_or_create(
                name=name,
                defaults={'vehicle': vehicle_type}
            )
            if not created and driver.vehicle != vehicle_type:
                driver.vehicle = vehicle_type
                driver.save()
            drivers[name] = driver
            action = "Created" if created else "Found"
            self.stdout.write(f'  {action} driver: {name} ({vehicle_type})')

        # -- Passenger List (from local_passenger_dumingag_test.pdf) --
        PASSENGERS = [
            "Aida Decierdo", "Aida Suaner", "Aida Sumalpong", "Albert Arapon",
            "Albert Mabisa", "Alberto Bautista", "Alberto Castro", "Alberto Fernandez",
            "Alberto Gonzales", "Alberto Gorre", "Alberto Tan", "Alfredo Domingo",
            "Alfredo Santiago", "Alfredo Santos", "Alfredo Villanueva", "Allan Garcia",
            "Allan Romero", "Allan Suerte", "Alma Romero", "Alma Sulatorio",
            "Alvin Decierdo", "Alvin Oranda", "Alvin Santos", "Analyn Sanchez",
            "Anita Oranda", "Anita Villanueva", "Anita dela Torre", "Antonio Gonzales",
            "Ariel Rote", "Ariel Santiago", "Ariel dela Cruz", "Arlyn Mendoza",
            "Arlyn Rote", "Arlyn dela Cruz", "Arnel Bautista", "Arnel Torres",
            "Arnel dela Torre", "Arnold Decierdo", "Arnold Suaner", "Arnold Torres",
            "Edgar Gutierrez", "Edgar Mabisa", "Edgardo Ramos", "Edgardo Suerte",
            "Eduardo Bautista", "Eduardo Castillo", "Eduardo Dela Cruz", "Eduardo Flores",
            "Eduardo Tan", "Elena Decierdo", "Elena Domingo", "Elena Mendoza",
            "Elena Salazar", "Elena Suaner", "Elena Sulatorio", "Elizabeth Flores",
            "Elizabeth Santiago", "Elizabeth Suaner", "Elizabeth Torres", "Elmer Andata",
            "Elmer Ramos", "Elmer Santos", "Elmer Suaner", "Elmer Suerte",
            "Elmer Torres", "Elsa Andata", "Elsa Oranda", "Emma Arsenal",
            "Emma Gonzales", "Emma Lim", "Emma Morales", "Emma Ticol",
            "Erlinda Ramos", "Evangeline Dico", "Evangeline Gonzales", "Evangeline Mercado",
            "Evelyn Gonzales", "Evelyn Ramos", "Evelyn Suaner", "Fe Castro",
            "Fe Torres", "Felix Andata", "Felix Castro", "Felix Fernandez",
            "Felix Mabisa", "Felix del Rosario", "Fernando Fernandez", "Fernando Suaner",
            "Fernando dela Cerna", "Francisco Arapon", "Francisco Dela Cruz",
            "Francisco dela Torre", "Gemma Dela Cruz", "Gemma Sumalpong",
            "Gina Andata", "Gina Dela Cruz", "Gloria del Rosario", "Grace Arapon",
            "Grace Oranda", "Grace Santos", "Helen dela Cruz", "Irene Lim",
            "Irene Torres", "Jaime Garcia", "Jaime Ramos", "Jaime Santos",
            "Jeffrey Lim", "Jeffrey Tan", "Jenelyn Mendoza", "Jennifer Bautista",
            "Jennifer Decierdo", "Jennifer Domingo", "Jennifer Rivera", "Jerry Torres",
            "Jesus Gonzales", "Jesus Maata", "Jesus Mercado", "Jesus Sanchez",
            "Jimmy Dico", "Jimmy Morales", "Jimmy Santos", "Jimmy Sumalpong",
            "Jocelyn Fernandez", "Jocelyn Mercado", "Jocelyn Rote", "Jocelyn Sanchez",
            "Joel Castillo", "Joel Dico", "Joel Torres", "John Castro",
            "Jonathan Castillo", "Jonathan Decierdo", "Jose Maata", "Jose Mendoza",
            "Jose dela Cruz", "Joseph Romero", "Joseph Torres", "Josephine Mabisa",
            "Josephine Ramos", "Josephine Romero", "Josephine Sanchez", "Josephine Tan",
            "Jovelyn Torres", "Jovelyn del Rosario", "Julieta Arsenal", "Julieta Decierdo",
            "Julieta Lim", "Julieta Morales", "Julito Santos", "Julito Sulatorio",
            "Julito Torres", "Leonardo Torres", "Lilia Bazar", "Lilia Dico",
            "Lilia Reyes", "Leonar do Torres", "Lorna Castillo", "Maria Gorre",
            "Maria Romero", "Maria Sulatorio", "Maria Sumalpong", "Maricel Lim",
            "Marilou Decierdo", "Marilou Santos", "Marilyn Ramos", "Mario Oranda",
            "Marites Arapon", "Marites Lim", "Marites Rivera", "Mark Oranda",
            "Mark Santiago", "Mark del Rosario", "Marlon Flores", "Marlon Gutierrez",
            "Marlon Santiago", "Marlon Santos", "Marlon dela Cruz", "Mary Arapon",
            "Mary Castillo", "Mary Torres", "Merlyn Lim", "Merlyn dela Torre",
            "Michael Gorre", "Michelle Dico", "Michelle Ramos", "Michelle Torres",
            "Michelle dela Cerna", "Myrna del Rosario", "Myrna dela Cruz",
            "Nelson Andata", "Nelson Aquino", "Nelson Arsenal", "Nelson Fernandez",
            "Nelson Flores", "Nelson Santos", "Nenita Bazar", "Nenita Sulatorio",
            "Nestor Arapon", "Noel Santos", "Norma Dela Cruz", "Norma Santos",
            "Norma Torres", "Pedro Bazar", "Rene Gutierrez", "Rey Tan",
            "Reynaldo Arapon", "Reynaldo Flores", "Reynaldo Gonzales", "Reynaldo Tan",
            "Reynaldo del Rosario", "Reynaldo dela Cerna", "Ricardo Arsenal",
            "Ricardo Mendoza", "Ricardo Oranda", "Ricardo Romero", "Ricardo Tan",
            "Richard Mendoza", "Ricky Mabisa", "Ricky Santos", "Ricky Sulatorio",
            "Ricky dela Cerna", "Robert Domingo", "Robert Ramos", "Roberto Aquino",
            "Roberto Morales", "Roberto Reyes", "Rodolfo Suerte", "Rodrigo Arsenal",
            "Rodrigo Garcia", "Roel Castillo", "Roel Flores", "Roel dela Cerna",
            "Rogelio Bautista", "Rogelio Oranda", "Rogelio Suerte", "Rogelio Sumalpong",
            "Rogelio dela Cerna", "Rolando Arapon", "Rolando Arsenal",
            "Rolando del Rosario", "Ronald Arapon", "Ronald Mercado", "Ronald Salazar",
            "Ronald Suaner", "Rosalie Lim", "Rosalie Ramos", "Rosalie Suerte",
            "Rosalinda Flores", "Rosalinda Mabisa", "Roselyn Andata", "Roselyn Lim",
            "Roselyn Torres", "Rosemarie Gutierrez", "Rosemarie Santos",
            "Rosemarie Suaner", "Rosita Dico", "Rowena Flores", "Rowena Mendoza",
            "Rowena Santos", "Ruben Flores", "Ruben Gutierrez", "Ruben Ramos",
            "Ruel Andata", "Ryan Gorre", "Ryan del Rosario", "Ryan dela Cerna",
            "Teresita Sumalpong", "Vicente Torres", "Vilma Dico", "Vilma Fernandez",
            "Vilma Flores", "Vilma Gutierrez", "Virginia Reyes", "Virginia Salazar",
            "Virginia dela Cerna", "Wilfredo Dela Cruz", "Wilfredo dela Torre",
        ]

        # -- Generate trips to consume exactly 480.00 liters --
        # Date range: April 14, 2026 to April 25, 2026 (12 days)
        START_DATE = date(2026, 4, 14)
        END_DATE = date(2026, 4, 25)
        num_days = (END_DATE - START_DATE).days + 1  # 12 days

        driver_names = list(drivers.keys())

        # -- Fixed liters per destination --
        LITERS_PER_DESTINATION = {
            'ozamiz_city': 20,
            'pagadian_city': 15,
        }

        # We need exactly 480L total.
        # 20x + 15y = 480  ->  x=12 ozamiz (240L) + y=16 pagadian (240L) = 480L
        NUM_OZAMIZ_TRIPS = 12
        NUM_PAGADIAN_TRIPS = 16
        TOTAL_TRIPS = NUM_OZAMIZ_TRIPS + NUM_PAGADIAN_TRIPS  # 28 trips

        # Build trip schedule
        random.seed(42)  # Reproducible randomness
        shuffled_passengers = PASSENGERS.copy()
        random.shuffle(shuffled_passengers)
        passenger_index = 0

        # Create the pool of destinations
        dest_pool = (['ozamiz_city'] * NUM_OZAMIZ_TRIPS) + (['pagadian_city'] * NUM_PAGADIAN_TRIPS)
        random.shuffle(dest_pool)

        # Create date-driver slots
        all_dates = [START_DATE + timedelta(days=i) for i in range(num_days)]

        # Distribute trips across dates and drivers
        trip_data = []
        dest_index = 0

        for trip_date in all_dates:
            if dest_index >= TOTAL_TRIPS:
                break
            # Randomly pick how many trips today (2-3 trips spread across drivers)
            day_drivers = driver_names.copy()
            random.shuffle(day_drivers)

            for drv_name in day_drivers:
                if dest_index >= TOTAL_TRIPS:
                    break
                # Each driver does 0 or 1 trip per day (randomly)
                if random.random() < 0.55:  # ~55% chance of a trip
                    dest = dest_pool[dest_index]
                    liters = LITERS_PER_DESTINATION[dest]
                    dest_index += 1

                    passenger = shuffled_passengers[passenger_index % len(shuffled_passengers)]
                    passenger_index += 1

                    trip_data.append((trip_date, passenger, drv_name, dest, liters))

        # If not all trips were assigned, distribute remaining across later dates
        while dest_index < TOTAL_TRIPS:
            for trip_date in all_dates:
                if dest_index >= TOTAL_TRIPS:
                    break
                day_drivers = driver_names.copy()
                random.shuffle(day_drivers)
                for drv_name in day_drivers:
                    if dest_index >= TOTAL_TRIPS:
                        break
                    # Check if this driver already has a trip on this date
                    existing = [t for t in trip_data if t[0] == trip_date and t[2] == drv_name]
                    if len(existing) < 2:  # Max 2 trips per driver per day
                        dest = dest_pool[dest_index]
                        liters = LITERS_PER_DESTINATION[dest]
                        dest_index += 1

                        passenger = shuffled_passengers[passenger_index % len(shuffled_passengers)]
                        passenger_index += 1

                        trip_data.append((trip_date, passenger, drv_name, dest, liters))

        # Sort trips by date, then driver name for consistency
        trip_data.sort(key=lambda x: (x[0], x[2]))

        total_planned_liters = round(sum(t[4] for t in trip_data), 2)
        total_planned_cost = round(total_planned_liters * PRICE_PER_LITER, 2)
        self.stdout.write(f'\n  Planned {len(trip_data)} trips totaling {total_planned_liters}L (P{total_planned_cost:,.2f})')

        # -- Create Records --
        self.stdout.write('\n' + '='*70)
        self.stdout.write('Creating fuel consumption records...')
        self.stdout.write('='*70)

        total_liters_created = 0
        total_cost_created = 0
        reference_number = 1
        trip_numbers = {}  # (driver_id, date) -> next trip number

        # Initialize vehicle balances
        vehicle_balances = {
            'Ambulance PTV': round(random.uniform(5, 15), 2),
            'Ambulance Province': round(random.uniform(5, 15), 2),
            'Ambulance DOH': round(random.uniform(5, 15), 2),
        }

        # Track last end time per driver per date for scheduling
        driver_last_end_times = {}

        for trip_date, passenger, driver_name, destination, liters in trip_data:
            driver = drivers[driver_name]
            trip_cost = round(liters * PRICE_PER_LITER, 2)
            vehicle_type = driver.vehicle

            # Trip number tracking per driver per date
            driver_date_key = (driver.id, trip_date)
            trip_number = trip_numbers.get(driver_date_key, 1)

            # Generate trip times
            travel_time = TRAVEL_TIMES.get(destination, timedelta(hours=1, minutes=15))

            # Reset end time tracking if new date for this driver
            date_key = (driver.id, trip_date)
            previous_end_time = driver_last_end_times.get(date_key)

            departure_time, arrival_time, return_departure_time, return_arrival_time = \
                self.generate_trip_times(travel_time, earliest_start_time=previous_end_time)

            if departure_time is None:
                self.stdout.write(self.style.ERROR(
                    f'  [ERR] Could not schedule trip for {passenger} on {trip_date} - no time slot available'
                ))
                continue

            driver_last_end_times[date_key] = return_arrival_time

            # Balance tracking
            starting_balance = vehicle_balances.get(vehicle_type, 10.0)
            consumed_liters = round(liters * random.uniform(0.9, 1.1), 2)
            finished_balance = round(starting_balance + liters - consumed_liters, 2)
            if finished_balance < 5:
                consumed_liters = round(starting_balance + liters - 8.0, 2)
                finished_balance = 8.0
            elif finished_balance > 25:
                consumed_liters = round(starting_balance + liters - 12.0, 2)
                finished_balance = 12.0
            vehicle_balances[vehicle_type] = finished_balance

            try:
                fuel_record = FuelConsumption(
                    driver=driver,
                    reference_number=reference_number,
                    date=trip_date,
                    trip_number=trip_number,
                    number_of_trips=1,
                    purpose='Transport Patient',
                    destination=destination,
                    vehicle=vehicle_type,
                    total_liters=liters,
                    cost=trip_cost,
                    actual_fuel_price=PRICE_PER_LITER,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    return_departure_time=return_departure_time,
                    return_arrival_time=return_arrival_time,
                    starting_balance=starting_balance,
                    consumed_liters=consumed_liters,
                    finished_balance=finished_balance,
                    passenger_name=passenger,
                )
                fuel_record._fuel_price = PRICE_PER_LITER
                fuel_record._bypass_fuel_limit = True
                fuel_record.save()

                total_liters_created += liters
                total_cost_created += trip_cost
                reference_number += 1
                trip_numbers[driver_date_key] = trip_number + 1

                city_display = destination.replace('_', ' ').title()
                self.stdout.write(
                    f'  [v] {trip_date} | {passenger:22} | {city_display:15} | '
                    f'{liters:6.2f}L x P{PRICE_PER_LITER:.2f} = P{trip_cost:10,.2f} | '
                    f'{driver.name} ({vehicle_type})'
                )

            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f'  [ERR] Validation: {e.messages}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERR] {str(e)}'))

        # Round totals for display
        total_liters_created = round(total_liters_created, 2)
        total_cost_created = round(total_cost_created, 2)

        # -- Summary --
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*70)
        self.stdout.write(f'  Total Budget:        P{TOTAL_BUDGET:,.2f}')
        self.stdout.write(f'  Fuel Price:          P{PRICE_PER_LITER:.2f}/liter')
        self.stdout.write(f'  Records Created:     {reference_number - 1}')
        self.stdout.write(f'  Total Liters:        {total_liters_created:.2f}L')
        self.stdout.write(f'  Total Cost:          P{total_cost_created:,.2f}')
        self.stdout.write(f'  Remaining Budget:    P{TOTAL_BUDGET - total_cost_created:,.2f}')
        self.stdout.write(f'  Budget Utilized:     {(total_cost_created / TOTAL_BUDGET * 100):.2f}%')
        self.stdout.write('='*70)

        # Per-driver breakdown
        self.stdout.write('\n' + self.style.SUCCESS('PER-DRIVER BREAKDOWN'))
        self.stdout.write('='*70)
        for name, driver in drivers.items():
            d_records = FuelConsumption.objects.filter(driver=driver)
            d_liters = d_records.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
            d_cost = d_records.aggregate(Sum('cost'))['cost__sum'] or 0
            d_count = d_records.count()
            self.stdout.write(
                f'  {name:30} ({driver.vehicle:20}) | {d_count:2} trips | '
                f'{d_liters:7.2f}L | P{d_cost:10,.2f}'
            )
        self.stdout.write('='*70)

        # Database verification
        db_count = FuelConsumption.objects.count()
        db_total_liters = FuelConsumption.objects.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
        db_total_cost = FuelConsumption.objects.aggregate(Sum('cost'))['cost__sum'] or 0

        self.stdout.write('\n' + self.style.SUCCESS('DATABASE VERIFICATION'))
        self.stdout.write('='*70)
        self.stdout.write(f'  Records in DB:       {db_count}')
        self.stdout.write(f'  Total Liters in DB:  {db_total_liters:.2f}L')
        self.stdout.write(f'  Total Cost in DB:    P{db_total_cost:,.2f}')
        self.stdout.write('='*70)

        if abs(db_total_liters - total_liters_created) < 0.01:
            self.stdout.write(self.style.SUCCESS('\n[OK] Data successfully populated and verified!'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[WARN] Verification mismatch!\n'
                    f'   Expected: {total_liters_created:.2f}L / P{total_cost_created:,.2f}\n'
                    f'   Found:    {db_total_liters:.2f}L / P{db_total_cost:,.2f}'
                )
            )

    def generate_trip_times(self, travel_time, earliest_start_time=None):
        """Generate realistic trip times based on travel duration."""
        work_start = time(6, 0)
        work_end = time(18, 0)

        earliest_start = datetime.combine(date.today(), work_start)

        if earliest_start_time:
            e_datetime = datetime.combine(date.today(), earliest_start_time) + timedelta(minutes=15)
            earliest_start = max(earliest_start, e_datetime)

        latest_start = datetime.combine(date.today(), work_end) - (travel_time * 2) - timedelta(hours=1)

        if latest_start > earliest_start:
            time_range_minutes = int((latest_start - earliest_start).total_seconds() / 60)
            random_minutes = random.randint(0, time_range_minutes)
            start_datetime = earliest_start + timedelta(minutes=random_minutes)
        else:
            if latest_start >= datetime.combine(date.today(), work_start):
                start_datetime = latest_start
            else:
                return None, None, None, None

        departure_time = start_datetime.time()
        arrival_datetime = start_datetime + travel_time
        arrival_time = arrival_datetime.time()

        rest_time = timedelta(minutes=random.randint(10, 30))
        return_departure_datetime = arrival_datetime + rest_time
        return_departure_time = return_departure_datetime.time()

        return_arrival_datetime = return_departure_datetime + travel_time
        return_arrival_time = return_arrival_datetime.time()

        return departure_time, arrival_time, return_departure_time, return_arrival_time
