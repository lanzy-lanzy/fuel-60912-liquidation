def fuel_form_view(request):
    context = {
        'office': 'MAYOR',
        'plate_number': 'ABC-123',
        'date': datetime.now(),
        'entries': FuelEntry.objects.all(),  # Assuming you have a FuelEntry model
        'total_diesel': FuelEntry.objects.aggregate(Sum('diesel_consumed'))['diesel_consumed__sum'],
        'total_gasoline': FuelEntry.objects.aggregate(Sum('gasoline_consumed'))['gasoline_consumed__sum'],
        'total_oil': FuelEntry.objects.aggregate(Sum('oil_used'))['oil_used__sum'],
        'total_grease': FuelEntry.objects.aggregate(Sum('grease_used'))['grease_used__sum'],
        'admin_officer': 'John Doe'
    }
    return render(request, 'fuel_form.html', context)