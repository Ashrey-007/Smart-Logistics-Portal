from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Booking, Complaint, Customer, Shipment, TransitLog


class Command(BaseCommand):
    help = "Create demo admin, customer, bookings, shipments, and complaints."

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@smartlogistics.local"})
        admin.set_password("admin12345")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        user, _ = User.objects.get_or_create(
            username="customer",
            defaults={"first_name": "Aarav", "last_name": "Shrestha", "email": "customer@example.com"},
        )
        user.set_password("customer12345")
        user.save()
        customer, _ = Customer.objects.get_or_create(user=user, defaults={"phone_number": "+977-9800000000", "address": "Kathmandu"})

        routes = [
            ("Electronics", 75, "Kathmandu", "Birgunj", Shipment.STATUS_TRANSIT, "Hetauda Hub", 40, 30, 30, 45000.0, "Priority"),
            ("Textiles", 140, "Lalitpur", "Pokhara", Shipment.STATUS_WAREHOUSE, "Kathmandu Warehouse", 120, 80, 60, 125000.0, "Standard"),
            ("Machine Parts", 220, "Biratnagar", "Bhairahawa", Shipment.STATUS_CUSTOMS, "Customs Desk", 60, 50, 50, 350000.0, "Express"),
        ]
        
        first_shipment = None
        for index, (cargo, weight, pickup, destination, status, location, l, w, h, val, service) in enumerate(routes, start=1):
            # Programmatic pricing for seed data
            vol_weight = (l * w * h) / 5000
            billable_weight = max(float(weight), float(vol_weight))
            base_cost = billable_weight * 1.50
            multipliers = {"Standard": 1.0, "Express": 1.5, "Priority": 2.5}
            est_cost = base_cost * multipliers[service] + val * 0.015

            booking, _ = Booking.objects.get_or_create(
                customer=customer,
                customer_name="Aarav Shrestha",
                phone_number="+977-9800000000",
                email="customer@example.com",
                cargo_type=cargo,
                weight=weight,
                pickup_location=pickup,
                destination=destination,
                pickup_date=timezone.localdate() + timedelta(days=index),
                defaults={
                    "booking_status": Booking.STATUS_APPROVED,
                    "length": l,
                    "width": w,
                    "height": h,
                    "declared_value": val,
                    "service_level": service,
                    "estimated_cost": est_cost,
                },
            )
            
            shipment, created = Shipment.objects.get_or_create(
                booking=booking,
                defaults={
                    "status": status,
                    "estimated_delivery_date": timezone.localdate() + timedelta(days=5 + index),
                    "current_location": location,
                },
            )
            
            # Clear any old log entries for re-run capability
            TransitLog.objects.filter(shipment=shipment).delete()

            # Seed realistic milestone tracking timeline history
            if status == Shipment.STATUS_TRANSIT:
                TransitLog.objects.create(
                    shipment=shipment,
                    location=pickup,
                    status=Shipment.STATUS_PENDING,
                    description="Booking request approved. Origin packaging and customs declarations initiated."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location=f"{pickup} Central Hub",
                    status=Shipment.STATUS_RECEIVED,
                    description="Cargo received at central logistics terminal. Underwent weighting, dimension scan, and sorting."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location=f"{pickup} Central Hub",
                    status=Shipment.STATUS_WAREHOUSE,
                    description="Cargo loaded in cargo bay container and palletized for road transit."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location="Hetauda Transit Hub",
                    status=Shipment.STATUS_TRANSIT,
                    description="Linehaul vehicle in transit. Arrived at Hetauda checkpoint gate."
                )
            elif status == Shipment.STATUS_WAREHOUSE:
                TransitLog.objects.create(
                    shipment=shipment,
                    location=pickup,
                    status=Shipment.STATUS_PENDING,
                    description="Booking approved. Scheduled carrier assignment."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location="Lalitpur Hub",
                    status=Shipment.STATUS_RECEIVED,
                    description="Cargo received from Lalitpur origin office."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location="Kathmandu Warehouse",
                    status=Shipment.STATUS_WAREHOUSE,
                    description="Cargo moved to central warehouse. Locked in Section B racking for consolidation."
                )
            elif status == Shipment.STATUS_CUSTOMS:
                TransitLog.objects.create(
                    shipment=shipment,
                    location=pickup,
                    status=Shipment.STATUS_PENDING,
                    description="Booking approved. Inter-province commercial clearance initiated."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location="Biratnagar Terminal",
                    status=Shipment.STATUS_RECEIVED,
                    description="Cargo received and processed."
                )
                TransitLog.objects.create(
                    shipment=shipment,
                    location="Customs Desk",
                    status=Shipment.STATUS_CUSTOMS,
                    description="Customs paperwork and transit manifest approved at regional customs desk."
                )
            
            first_shipment = first_shipment or shipment

        Complaint.objects.get_or_create(
            customer=customer,
            tracking_id=first_shipment.tracking_id,
            complaint_type="Delivery Delay",
            defaults={"message": "Please confirm revised ETA for this shipment."},
        )
        self.stdout.write(self.style.SUCCESS("Sample data created."))
        self.stdout.write("Admin: admin / admin12345")
        self.stdout.write("Customer: customer / customer12345")
