from fuel.models import FuelConsumption
from django.db.models import Count

def verify_rotation():
    print("Driver Rotation Verification (2-on, 2-off)\n")
    
    dates = FuelConsumption.objects.order_by('date').values_list('date', flat=True).distinct()
    
    for current_date in dates:
        print(f"Date: {current_date}")
        drivers_on_date = FuelConsumption.objects.filter(date=current_date).values_list('driver__name', flat=True).distinct()
        for driver in drivers_on_date:
            print(f"  - {driver}")
        print("-" * 20)

if __name__ == "__main__":
    verify_rotation()
