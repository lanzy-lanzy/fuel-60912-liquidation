from django.contrib import admin
from .models import Driver, FuelConsumption, Vehicle, LiquidationSetting, LiquidationReport, LiquidationReportEntry, PettyCashVoucher, ReimbursementExpenseReceipt
from django.utils.html import format_html

class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle')
    list_filter = ('vehicle',)
    search_fields = ('name', 'vehicle')
    list_per_page = 20

    fieldsets = (
        ('Driver Information', {
            'fields': ('name', 'vehicle')
        }),
    )

class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'plate_number')
    search_fields = ('name', 'plate_number')
    list_per_page = 20

class FuelConsumptionAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'date', 'driver_info', 'vehicle', 'destination_display', 
                   'purpose', 'or_number', 'total_liters', 'cost_display', 'number_of_trips')
    list_filter = ('date', 'vehicle', 'destination', 'purpose')
    search_fields = ('driver__name', 'reference_number', 'vehicle', 'or_number')
    readonly_fields = ('reference_number',)
    list_per_page = 50
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Trip Information', {
            'fields': ('reference_number', 'date', 'driver', 'vehicle', 'purpose', 'destination', 'or_number')
        }),
        ('Fuel Details', {
            'fields': ('total_liters', 'cost', 'number_of_trips')
        })
    )
    
    def destination_display(self, obj):
        return dict(FuelConsumption.DESTINATION_CHOICES).get(obj.destination, obj.destination)
    destination_display.short_description = 'Destination'
    destination_display.admin_order_field = 'destination'
    
    def cost_display(self, obj):
        return f'₱{obj.cost:,.2f}'
    cost_display.short_description = 'Cost'
    cost_display.admin_order_field = 'cost'
    
    def driver_info(self, obj):
        return f"{obj.driver.name} ({obj.driver.vehicle})" if obj.driver else ""
    driver_info.short_description = 'Driver (Vehicle)'
    
    def save_model(self, request, obj, form, change):
        if not obj.reference_number:
            # Get the highest reference number and increment it
            last_ref = FuelConsumption.objects.order_by('-reference_number').first()
            obj.reference_number = last_ref.reference_number + 1 if last_ref else 1
        super().save_model(request, obj, form, change)

# Register models with their admin classes
admin.site.register(Driver, DriverAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(FuelConsumption, FuelConsumptionAdmin)

class LiquidationSettingAdmin(admin.ModelAdmin):
    list_display = ('pk', 'principal_amount', 'check_number')

admin.site.register(LiquidationSetting, LiquidationSettingAdmin)

class LiquidationReportEntryInline(admin.TabularInline):
    model = LiquidationReportEntry
    extra = 0

class LiquidationReportAdmin(admin.ModelAdmin):
    list_display = ('pk', 'no', 'report_date', 'principal_amount', 'check_number', 'created_at')
    list_filter = ('report_date',)
    inlines = [LiquidationReportEntryInline]

admin.site.register(LiquidationReport, LiquidationReportAdmin)

@admin.register(PettyCashVoucher)
class PettyCashVoucherAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'voucher_date', 'payee_office', 'amount', 'purpose', 'created_at')
    list_filter = ('voucher_date',)
    search_fields = ('voucher_no', 'payee_office', 'particulars')
    date_hierarchy = 'voucher_date'

@admin.register(ReimbursementExpenseReceipt)
class ReimbursementExpenseReceiptAdmin(admin.ModelAdmin):
    list_display = ('rer_no', 'receipt_date', 'received_from_name', 'amount_in_figures', 'petty_cash_voucher', 'created_at')
    list_filter = ('receipt_date',)
    search_fields = ('rer_no', 'received_from_name', 'entity_name')
    date_hierarchy = 'receipt_date'
    readonly_fields = ('attached_image_preview',)

    def attached_image_preview(self, obj):
        if obj.attached_image:
            return format_html('<img src="{}" style="max-height:120px; border:1px solid #e2e8f0;" />', obj.attached_image.url)
        return "No image"
    attached_image_preview.short_description = "Image preview"
