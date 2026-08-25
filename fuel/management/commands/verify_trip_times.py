from fuel.models import FuelConsumption
from datetime import datetime, date

def verify_trip_times():
    print("Verifying trip times for overlaps...")
    records = FuelConsumption.objects.all().order_by('date', 'driver', 'departure_time')
    
    overlaps_found = 0
    driver_trips = {}
    
    for r in records:
        key = (r.driver_id, r.date)
        if key not in driver_trips:
            driver_trips[key] = []
        driver_trips[key].append(r)
        
    for key, trips in driver_trips.items():
        if len(trips) > 1:
            for i in range(len(trips) - 1):
                t1 = trips[i]
                t2 = trips[i+1]
                
                # Convert time to fixed dummy datetime for comparison to avoid date mismatch errors
                dummy_date = date(2000, 1, 1)
                end1 = datetime.combine(dummy_date, t1.return_arrival_time)
                start2 = datetime.combine(dummy_date, t2.departure_time)
                
                if start2 < end1:
                    print(f"OVERLAP FOUND: Driver {t1.driver.name} on {t1.date}")
                    print(f"  Trip {t1.trip_number}: {t1.departure_time} - {t1.return_arrival_time}")
                    print(f"  Trip {t2.trip_number}: {t2.departure_time} - {t2.return_arrival_time}")
                    overlaps_found += 1
                elif (start2 - end1).total_seconds() < 900: # 15 mins
                    # This is fine, but good to know
                    pass

    if overlaps_found == 0:
        print("SUCCESS: No overlapping trips found!")
    else:
        print(f"FAILURE: Found {overlaps_found} overlapping trip segments.")

if __name__ == "__main__":
    verify_trip_times()