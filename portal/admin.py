from django.contrib import admin

from .models import Booking, Complaint, Customer, Shipment, TransitLog


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "address", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone_number")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "cargo_type", "destination", "booking_status", "created_at")
    list_filter = ("booking_status", "cargo_type")
    search_fields = ("customer_name", "email", "phone_number", "destination")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_id", "status", "estimated_delivery_date", "current_location")
    list_filter = ("status",)
    search_fields = ("tracking_id", "booking__customer_name")
    readonly_fields = ("tracking_id",)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("tracking_id", "complaint_type", "complaint_status", "created_at")
    list_filter = ("complaint_status", "complaint_type")
    search_fields = ("tracking_id", "message")


@admin.register(TransitLog)
class TransitLogAdmin(admin.ModelAdmin):
    list_display = ("shipment", "location", "status", "timestamp")
    list_filter = ("status",)
    search_fields = ("shipment__tracking_id", "location", "description")
