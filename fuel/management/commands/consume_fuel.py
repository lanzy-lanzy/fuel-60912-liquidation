import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.db.models import Sum
from fuel.models import Driver, FuelConsumption

class Command(BaseCommand):
    help = 'Reset database and populate 500,000 budget @ 90.00/liter (diesel). Ambulance is the main fuel consumer; HE road clearing (landslide) is rare/random, each truck consuming 200-300L/day grouped by barangay, Jun 18 - Sep 8, 2026'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all existing fuel consumption and driver records'
        )

    def handle(self, *args, **kwargs):
        if not kwargs['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  This command will DELETE all existing FuelConsumption and Driver records!\n'
                    'To proceed, run: python manage.py consume_fuel --confirm'
                )
            )
            return

        # Clear all existing records for a fresh database
        old_consumption_count = FuelConsumption.objects.count()
        old_driver_count = Driver.objects.count()
        FuelConsumption.objects.all().delete()
        Driver.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Cleared {old_consumption_count} FuelConsumption and {old_driver_count} Driver records'
            )
        )

        # Budget and fuel price
        TOTAL_BUDGET = 500000.00
        PRICE_PER_LITER = 90.00  # diesel

        # Budget split: ambulance is the main fuel consumer; heavy equipment is
        # only for bigger utilization (rare landslide clearing)
        AMB_BUDGET = 350000.00
        HE_BUDGET = TOTAL_BUDGET - AMB_BUDGET  # 150,000

        # Heavy equipment drivers (road clearing / landslide response)
        driver_shifts = {
            "GRADER": [
                ("NESTOR GONZALES", "Grader XCMG- GR165")
            ],
            "DUMPTRACK": [
                ("RAYMOND HANGCAN", "SINOTRUCK F 318"),
                ("JOMAR BADILLES", "Dumptruck HOWO M7 F030"),
                ("MAYOLITO CULANAG", "DUMPTRUCK GREEN NO PLATE"),
                ("Ariel canada", "SINOTRUCK 372"),
                ("Junel bonsoa", "HOWO M6 772")
            ],
            "BACKHOE": [
                ("MARK JOSEPH QUINALAGAN", "LONGKING"),
                ("Robin repaldo", "MINI BACKHOE XE60DA")
            ]
        }

        # Ambulance driver shifts (also part of fuel consumption)
        ambulance_shifts = {
            "Ambulance PTV": [
                ("Grace Zaldy Matos", "Ambulance PTV"),
                ("Aldren Urot", "Ambulance PTV")
            ],
            "Ambulance DOH": [
                ("Jeweriel Sulatorio", "Ambulance DOH"),
                ("Antonio Tenebro", "Ambulance DOH"),
                ("Jessie Aradellos", "Ambulance DOH"),
            ],
            "Ambulance L300": [
                ("Julchan Mamac", "Ambulance L300"),
                ("Edwin Tac-an", "Ambulance L300")
            ],
            "Ambulance Province": [
                ("Antonio Tenebro", "Ambulance Province"),
                ("Humphrey Daryl Ginggo", "Ambulance Province")
            ]
        }

        # Create or update drivers
        he_drivers = []
        for vehicle, driver_list in driver_shifts.items():
            for name, vehicle_type in driver_list:
                driver, created = Driver.objects.get_or_create(
                    name=name,
                    defaults={'vehicle': vehicle_type}
                )
                if not created and driver.vehicle != vehicle_type:
                    driver.vehicle = vehicle_type
                    driver.save()
                he_drivers.append(driver)

        drivers_by_vehicle = {}
        for vehicle, driver_list in ambulance_shifts.items():
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

        # Barangay assignments with separate date windows
        barangay_ranges = [
            ('Calumangi', date(2026, 6, 18), date(2026, 6, 30)),
            ('Danlugan', date(2026, 7, 1), date(2026, 7, 14)),
            ('Saad', date(2026, 7, 15), date(2026, 7, 28)),
            ('Salvador', date(2026, 7, 29), date(2026, 8, 11)),
            ('San Juan', date(2026, 8, 12), date(2026, 8, 25)),
            ('Bagong Kauswagan', date(2026, 8, 26), date(2026, 9, 8)),
        ]

        total_days = sum((end - start).days + 1 for _, start, end in barangay_ranges)

        self.stdout.write('\n' + '='*60)
        self.stdout.write('Fuel Consumption - Mainly Ambulance Trips + Rare Landslide Road Clearing')
        self.stdout.write(f'Budget: ₱{TOTAL_BUDGET:,.2f} @ ₱{PRICE_PER_LITER:.2f}/liter')
        self.stdout.write(f'Period: June 18 - September 8, 2026 ({total_days} days)')
        self.stdout.write(f'  Ambulance budget: ₱{AMB_BUDGET:,.2f}')
        self.stdout.write(f'  HE budget:       ₱{HE_BUDGET:,.2f}')
        self.stdout.write('='*60)

        # Track totals
        total_liters = 0
        total_cost = 0
        he_consumed = 0
        amb_consumed = 0

        reference_number = 1
        trip_numbers = {}  # Track trip numbers per driver per date

        def create_record(driver, day, liters, destination, purpose, travel_hours=2):
            nonlocal total_liters, total_cost, reference_number

            if liters <= 0:
                return

            cost = round(liters * PRICE_PER_LITER, 2)
            driver_date_key = (driver.id, day)
            trip_number = trip_numbers.get(driver_date_key, 1)

            departure_time, arrival_time, return_departure_time, return_arrival_time = self.generate_trip_times(timedelta(hours=travel_hours))

            fuel_record = FuelConsumption(
                driver=driver,
                reference_number=reference_number,
                date=day,
                trip_number=trip_number,
                number_of_trips=1,
                purpose=purpose,
                destination=destination,
                vehicle=driver.vehicle,
                total_liters=liters,
                cost=cost,
                actual_fuel_price=PRICE_PER_LITER,
                departure_time=departure_time,
                arrival_time=arrival_time,
                return_departure_time=return_departure_time,
                return_arrival_time=return_arrival_time,
                starting_balance=round(random.uniform(20, 50), 2),
                consumed_liters=round(liters * random.uniform(0.9, 1.0), 2),
                finished_balance=round(random.uniform(10, 30), 2),
                passenger_name=None
            )
            fuel_record._fuel_price = PRICE_PER_LITER
            fuel_record._bypass_fuel_limit = True
            fuel_record.save()

            total_liters += liters
            total_cost += cost
            reference_number += 1
            trip_numbers[driver_date_key] = trip_number + 1

        # --- Heavy equipment: rare/random landslide clearing, 200-300 L/truck/day ---
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Heavy Equipment - Landslide Clearing (grouped by barangay)')
        self.stdout.write('='*60)

        he_liters_target = HE_BUDGET / PRICE_PER_LITER

        # Landslides are rare: a few barangays get one group trip each (no
        # duplicate barangay). On that barangay's trip day a group of different
        # trucks (sinotruck, howo, longking, mini backhoe, ...) all operate, each
        # truck used exactly once and consuming 200-300 L.
        total_truck_days = random.randint(7, 8)
        n_groups = random.randint(3, min(4, len(barangay_ranges)))
        selected = random.sample(barangay_ranges, n_groups)

        # Split total truck-days into per-barangay group sizes (2-3 trucks each)
        group_sizes = [2] * n_groups
        leftover = total_truck_days - sum(group_sizes)
        for i in range(leftover):
            group_sizes[i % n_groups] += 1

        # Build per-truck liters that always stay in 200-300 L and sum to the
        # exact HE budget
        day_liters_list = []
        remaining = he_liters_target
        for i in range(total_truck_days):
            left = total_truck_days - i
            if left == 1:
                liters = remaining
            else:
                min_l = max(200, remaining - 300 * (left - 1))
                max_l = min(300, remaining - 200 * (left - 1))
                if min_l > max_l:
                    min_l, max_l = 200, 300
                liters = random.uniform(min_l, max_l)
            liters = round(liters, 2)
            day_liters_list.append(liters)
            remaining = round(remaining - liters, 2)
        day_liters_list[-1] = round(he_liters_target - sum(day_liters_list[:-1]), 2)

        lit_idx = 0
        all_trucks = random.sample(he_drivers, total_truck_days)  # each truck used exactly once
        truck_idx = 0
        for (name, start, end), gsize in zip(selected, group_sizes):
            # One group trip day per barangay; a distinct group of trucks on that day
            day = start + timedelta(days=random.randint(0, (end - start).days))
            trucks = all_trucks[truck_idx:truck_idx + gsize]
            truck_idx += gsize
            self.stdout.write(f'\n  Group trip: {name} on {day.strftime("%b %d")} ({gsize} trucks)')
            for driver in trucks:
                liters = day_liters_list[lit_idx]
                lit_idx += 1
                create_record(
                    driver, day, liters, name,
                    'Road Clearing Operation (Landslide)', travel_hours=2
                )
                he_consumed += liters * PRICE_PER_LITER
                self.stdout.write(
                    f'    ✓ {name:20} - {driver.vehicle:30} {liters:6.1f}L × ₱{PRICE_PER_LITER:.2f} = '
                    f'₱{liters * PRICE_PER_LITER:10,.2f} ({driver.name})'
                )

        # --- Ambulance trips: MAIN fuel consumer, spread across the whole period ---
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Ambulance Trips (Patient Transport) - Main Consumer')
        self.stdout.write('='*60)

        city_fuel_data = [
            ('ozamiz_city', 25),
            ('pagadian_city', 20),
            ('dipolog', 30),
            ('zamboanga_city', 60),
            ('cagayan', 60),
            ('margosatubig', 40),
        ]
        travel_times = {
            'pagadian_city': timedelta(hours=1, minutes=10),
            'ozamiz_city': timedelta(hours=1, minutes=20),
            'dipolog': timedelta(hours=2, minutes=0),
            'zamboanga_city': timedelta(hours=5, minutes=0),
            'cagayan': timedelta(hours=4, minutes=0),
            'margosatubig': timedelta(hours=3, minutes=10),
        }
        vehicle_types = ['Ambulance PTV', 'Ambulance DOH', 'Ambulance L300', 'Ambulance Province']
        vehicle_balances = {
            vt: round(random.uniform(5, 15), 2) for vt in vehicle_types
        }

        start_date = barangay_ranges[0][1]
        end_date = barangay_ranges[-1][2]
        period_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Ambulance trips are the main consumer: most days get 1-2 trips with
        # occasional gaps so the ambulance drivers stay busy but not exhausted
        amb_remaining = AMB_BUDGET
        amb_records = 0
        selection_index = 0  # cycles vehicles so every ambulance vehicle/driver gets trips
        vehicle_rotation = {vt: 0 for vt in vehicle_types}  # per-vehicle driver rotation

        for day in period_days:
            if amb_remaining <= 0:
                break

            # Most days 1-2 trips, occasional no-trip days for realism
            r = random.random()
            if r < 0.15:
                n_trips_today = 0
            elif r < 0.60:
                n_trips_today = 1
            else:
                n_trips_today = 2

            for _ in range(n_trips_today):
                if amb_remaining <= 0:
                    break

                dest, base_liters = random.choice(city_fuel_data)
                liters = round(base_liters * random.uniform(0.9, 1.1), 2)
                cost = round(liters * PRICE_PER_LITER, 2)

                # Rotate through vehicle types so every ambulance is used
                current_vehicle_type = vehicle_types[selection_index % len(vehicle_types)]
                selection_index += 1

                # Rotate within the vehicle's driver pair so every driver gets trips
                pair = drivers_by_vehicle[current_vehicle_type]
                driver = pair[vehicle_rotation[current_vehicle_type] % len(pair)]
                vehicle_rotation[current_vehicle_type] += 1

                driver_date_key = (driver.id, day)
                if driver_date_key in trip_numbers:
                    continue

                if cost > amb_remaining:
                    # Not enough for a full regular trip; consume the remainder in the
                    # final ambulance record below instead
                    continue

                create_record(
                    driver, day, liters, dest, 'Transport Patient',
                    travel_hours=travel_times.get(dest, timedelta(hours=1, minutes=15)).total_seconds() / 3600
                )
                amb_remaining = round(amb_remaining - cost, 2)
                amb_consumed += cost
                amb_records += 1
                self.stdout.write(
                    f'  ✓ AMB: {dest.replace("_", " ").title():25} - {liters:5.1f}L × ₱{PRICE_PER_LITER:.2f} = '
                    f'₱{cost:10,.2f} ({driver.name})'
                )

        # Consume any remaining ambulance budget with a final trip so the full
        # 500k is utilized
        if amb_remaining > 1:
            day = period_days[-1]
            # Assign to an ambulance driver who has the fewest trips so all get coverage
            amb_drivers = [
                d for d in Driver.objects.filter(vehicle__startswith='Ambulance')
            ]
            driver = min(
                amb_drivers,
                key=lambda d: FuelConsumption.objects.filter(driver=d).count()
            )
            while (driver.id, day) in trip_numbers:
                day -= timedelta(days=1)

            final_liters = round(amb_remaining / PRICE_PER_LITER, 2)
            create_record(
                driver, day, final_liters, random.choice(city_fuel_data)[0], 'Transport Patient',
                travel_hours=1.5
            )
            amb_consumed += final_liters * PRICE_PER_LITER
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ AMB final: consumed remaining ₱{amb_remaining:,.2f} on {day} ({driver.name})'
                )
            )

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total Budget:            ₱{TOTAL_BUDGET:,.2f}')
        self.stdout.write(f'Total Consumed:          ₱{total_cost:,.2f}')
        self.stdout.write(f'Total Liters:            {total_liters:,.2f} L @ ₱{PRICE_PER_LITER:.2f}')
        self.stdout.write(f'Records Created:         {reference_number - 1}')
        self.stdout.write(f'  - HE Cost:             ₱{he_consumed:,.2f}')
        self.stdout.write(f'  - Ambulance Cost:      ₱{amb_consumed:,.2f}')
        self.stdout.write('='*60)

        # Final precise adjustment so total cost equals exactly the budget
        db_total_cost = FuelConsumption.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        adjustment = round(TOTAL_BUDGET - db_total_cost, 2)
        if abs(adjustment) > 0.001:
            last_record = FuelConsumption.objects.order_by('-id').first()
            if last_record:
                new_cost = round(last_record.cost + adjustment, 2)
                new_liters = round(last_record.total_liters + (adjustment / PRICE_PER_LITER), 2)
                FuelConsumption.objects.filter(id=last_record.id).update(
                    total_liters=new_liters,
                    cost=new_cost,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Final adjustment: +₱{adjustment:,.2f} applied to {last_record.driver.name} on '
                        f'{last_record.date} (ref #{last_record.reference_number})'
                    )
                )

        # Per-barangay breakdown
        self.stdout.write('\nPer-Barangay Consumption:')
        for name, start, end in barangay_ranges:
            qs = FuelConsumption.objects.filter(destination=name)
            brgy_cost = qs.aggregate(Sum('cost'))['cost__sum'] or 0
            brgy_liters = qs.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
            brgy_count = qs.count()
            brgy_days = sorted(set(qs.values_list('date', flat=True)))
            self.stdout.write(
                f'  {name:20} ₱{brgy_cost:>12,.2f} | {brgy_liters:>8,.2f} L | {brgy_count} records | '
                f'{len(brgy_days)} day(s)'
            )

        amb_qs = FuelConsumption.objects.filter(driver__vehicle__startswith='Ambulance')
        amb_cost = amb_qs.aggregate(Sum('cost'))['cost__sum'] or 0
        amb_liters = amb_qs.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
        self.stdout.write(
            f'  {"Ambulance Trips":20} ₱{amb_cost:>12,.2f} | {amb_liters:>8,.2f} L | {amb_qs.count()} records'
        )

        # Database check
        db_count = FuelConsumption.objects.count()
        db_total_cost = FuelConsumption.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        db_total_liters = FuelConsumption.objects.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'DB Records:              {db_count}')
        self.stdout.write(f'DB Total Cost:           ₱{db_total_cost:,.2f}')
        self.stdout.write(f'DB Total Liters:         {db_total_liters:,.2f} L')
        if db_total_liters:
            self.stdout.write(f'DB Price Check:          ₱{db_total_cost / db_total_liters:,.2f}/L')
        self.stdout.write('='*60)

    def generate_trip_times(self, travel_time):
        """
        Generate realistic trip times based on travel duration.
        """
        # Working hours (6:00 AM to 6:00 PM)
        work_start = time(6, 0)
        work_end = time(18, 0)

        # Generate a random start time within working hours
        # But ensure there's enough time for the round trip
        earliest_start = datetime.combine(date.today(), work_start)
        latest_start = datetime.combine(date.today(), work_end) - (travel_time * 2) - timedelta(hours=1)

        if latest_start > earliest_start:
            # Generate a random start time within the valid range
            time_range_minutes = int((latest_start - earliest_start).total_seconds() / 60)
            random_minutes = random.randint(0, time_range_minutes)
            start_datetime = earliest_start + timedelta(minutes=random_minutes)
        else:
            # Fallback if there's not enough time
            start_datetime = earliest_start

        departure_time = start_datetime.time()

        # Calculate arrival time
        arrival_datetime = start_datetime + travel_time
        arrival_time = arrival_datetime.time()

        # Add rest time at destination (10-30 minutes)
        rest_time = timedelta(minutes=random.randint(10, 30))
        return_departure_datetime = arrival_datetime + rest_time
        return_departure_time = return_departure_datetime.time()

        # Calculate return arrival time
        return_arrival_datetime = return_departure_datetime + travel_time
        return_arrival_time = return_arrival_datetime.time()

        return departure_time, arrival_time, return_departure_time, return_arrival_time