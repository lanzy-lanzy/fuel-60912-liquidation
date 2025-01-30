from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Sum
from .models import Driver, FuelConsumption
from .forms import FuelConsumptionForm
from datetime import date, datetime, timedelta  # Ensure timedelta is imported
import calendar
class DashboardView(ListView):
    template_name = 'fuel/dashboard.html'
    context_object_name = 'fuel_entries'
    
    def get_queryset(self):
        return FuelConsumption.objects.order_by('-date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate fuel statistics
        total_consumed = FuelConsumption.objects.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        total_fuel = 7499.68
        remaining_fuel = total_fuel - total_consumed
        total_cost = FuelConsumption.objects.aggregate(
            Sum('cost')
        )['cost__sum'] or 0

        context.update({
            'total_consumed': round(total_consumed, 2),
            'remaining_fuel': round(remaining_fuel, 2),
            'remaining_percentage': round((remaining_fuel / total_fuel) * 100, 1),
            'total_cost': round(total_cost, 2),
            'drivers': Driver.objects.annotate(
                total_used=Sum('fuelconsumption__total_liters')
            ),
            'current_month': datetime.now().strftime('%B')
        })
        return context

class DriverListView(ListView):
    model = Driver
    template_name = 'fuel/driver_list.html'
    context_object_name = 'drivers'

class DriverDetailView(DetailView):
    model = Driver
    template_name = 'fuel/driver_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        driver = self.object
        
        consumption_data = FuelConsumption.objects.filter(
            driver=driver
        ).order_by('date')
        
        total_used = consumption_data.aggregate(
            Sum('total_liters')
        )['total_liters__sum'] or 0
        
        context.update({
            'consumption_history': consumption_data,
            'total_trips': consumption_data.aggregate(
                Sum('number_of_trips')
            )['number_of_trips__sum'],
            'total_used': round(total_used, 2),
            'average_per_trip': round(total_used / sum(
                c.number_of_trips for c in consumption_data
            ), 2) if consumption_data else 0
        })
        return context

# views.py
class FuelConsumptionCreateView(CreateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = 'fuel/fuel_form.html'

    def get_success_url(self):
        return reverse('gas_slip', kwargs={'pk': self.object.pk})
class FuelConsumptionUpdateView(UpdateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = 'fuel/fuel_form.html'
    success_url = reverse_lazy('dashboard')

class FuelConsumptionDeleteView(DeleteView):
    model = FuelConsumption
    template_name = 'fuel/fuel_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

def fuel_report(request):
    # Calculate weekly consumption
    start_date = date(2024, 10, 13)
    end_date = date(2024, 12, 31)
    
    consumption_data = FuelConsumption.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Create weekly breakdown
    weekly_report = []
    current_week = []
    current_week_start = start_date
    
    for entry in consumption_data:
        while entry.date >= current_week_start + timedelta(days=7):  # Use timedelta here
            weekly_report.append({
                'week_start': current_week_start,
                'total_liters': sum(c.total_liters for c in current_week),
                'total_cost': sum(c.cost for c in current_week)
            })
            current_week = []
            current_week_start += timedelta(days=7)  # Use timedelta here
        
        current_week.append(entry)
    
    # Add remaining week
    if current_week:
        weekly_report.append({
            'week_start': current_week_start,
            'total_liters': sum(c.total_liters for c in current_week),
            'total_cost': sum(c.cost for c in current_week)
        })
    
    # Calculate remaining days
    today = date.today()
    remaining_days = (end_date - today).days if today < end_date else 0
    
    # Calculate average daily consumption
    total_days = (end_date - start_date).days
    days_passed = (today - start_date).days if today > start_date else 0
    avg_daily = (FuelConsumption.objects.aggregate(
        Sum('total_liters')
    )['total_liters__sum'] or 0) / days_passed if days_passed > 0 else 0
    
    context = {
        'weekly_report': weekly_report,
        'remaining_days': remaining_days,
        'avg_daily': round(avg_daily, 2),
        'projected_use': round(avg_daily * remaining_days, 2),
    }
    
    return render(request, 'fuel/fuel_report.html', context)# views.py
class DriverCreateView(CreateView):
    model = Driver
    fields = ['name']
    template_name = 'fuel/driver_form.html'
    success_url = reverse_lazy('driver_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        return response
# fuel/views.py
from django.views.generic import DetailView
from .models import FuelConsumption

class GasSlipView(DetailView):
        model = FuelConsumption
        template_name = 'fuel/gas_slip.html'
        context_object_name = 'object'

# fuel/views.py

from django.shortcuts import render
from .models import FuelConsumption

def gas_slip_print_view(request):
    slips = FuelConsumption.objects.all().order_by('date')
    context = {
        'slips': slips
    }
    return render(request, 'fuel/gas_slip_print.html', context)
