from django.urls import path
from .views import (
    DashboardView,
    DriverListView,
    DriverDetailView,
    FuelConsumptionCreateView,
    FuelConsumptionUpdateView,
    FuelConsumptionDeleteView,
    DriverCreateView,
    GasSlipView,
    fuel_report,
    gas_slip_print_view,

)



urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name='dashboard'),
    
    # Drivers
    path('drivers/', DriverListView.as_view(), name='driver_list'),
    path('drivers/<int:pk>/', DriverDetailView.as_view(), name='driver_detail'),
    
    # Fuel Consumption CRUD
    path('entries/new/', FuelConsumptionCreateView.as_view(), name='fuelconsumption_create'),
    path('entries/<int:pk>/edit/', FuelConsumptionUpdateView.as_view(), name='fuelconsumption_update'),
    path('entries/<int:pk>/delete/', FuelConsumptionDeleteView.as_view(), name='fuelconsumption_delete'),
    
    # Reports
    path('report/', fuel_report, name='fuel_report'),
    path('drivers/new/', DriverCreateView.as_view(), name='driver_create'),
     path('gas-slip/<int:pk>/', GasSlipView.as_view(), name='gas_slip'),

      path('print-gas-slips/', gas_slip_print_view, name='print_gas_slips'),
  ]
