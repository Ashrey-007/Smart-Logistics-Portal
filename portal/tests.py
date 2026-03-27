from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from portal.models import Customer, Booking, Shipment, TransitLog

class PortalSmokeTests(TestCase):
    def test_home_loads(self):
        self.assertEqual(self.client.get("/").status_code, 200)

class LogisticsOperationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_customer",
            email="test@example.com",
            password="testpassword123"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number="+977-9800000000",
            address="Kathmandu"
        )

    def test_booking_volumetric_pricing_calculation(self):
        """
        Verifies that our volumetric pricing equation correctly computes bases, multipliers, and insurance surcharges.
        """
        self.client.login(username="test_customer", password="testpassword123")
        
        response = self.client.post("/booking/new/", {
            "customer_name": "Aarav Shrestha",
            "phone_number": "+977-9800000000",
            "email": "test@example.com",
            "cargo_type": "Electronics",
            "weight": "75.00",
            "pickup_location": "Kathmandu",
            "destination": "Birgunj",
            "pickup_date": "2026-06-01",
            "length": "40.00",
            "width": "30.00",
            "height": "30.00",
            "declared_value": "45000.00",
            "service_level": "Priority"
        })
        
        # Verify redirect to history list upon success
        self.assertEqual(response.status_code, 302)
        
        # Assert database details
        booking = Booking.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(booking)
        
        # Volumetric weight = (40 * 30 * 30) / 5000 = 7.2 kg
        # Max of (75 kg scale mass vs 7.2 kg volume) = 75 kg billable weight
        # Base fee = 75 * 1.50 = 112.50 NPR
        # Priority multiplier = 2.5. Base * 2.5 = 281.25 NPR
        # Surcharge cover = 45000 * 0.015 = 675.00 NPR
        # Total expected = 281.25 + 675.00 = 956.25 NPR
        expected_cost = Decimal("956.25")
        self.assertAlmostEqual(booking.estimated_cost, expected_cost, places=2)

    def test_transit_logging_upon_shipment_update(self):
        """
        Verifies that updating a shipment via the staff form automatically records a TransitLog milestone checkpoint.
        """
        # Create mock approved booking
        booking = Booking.objects.create(
            customer=self.customer,
            customer_name="Aarav Shrestha",
            phone_number="+977-9800000000",
            email="test@example.com",
            cargo_type="Machine Parts",
            weight=Decimal("12.00"),
            pickup_location="Biratnagar",
            destination="Bhairahawa",
            pickup_date="2026-06-01",
            booking_status=Booking.STATUS_APPROVED
        )
        
        # Spin up shipment
        shipment = Shipment.objects.create(
            booking=booking,
            status=Shipment.STATUS_RECEIVED,
            current_location="Biratnagar Terminal"
        )
        
        # Log in as administrator/staff
        User.objects.create_superuser(
            username="admin_staff",
            email="staff@smartlogistics.local",
            password="adminpassword123"
        )
        self.client.login(username="admin_staff", password="adminpassword123")
        
        # Post shipment milestone update
        response = self.client.post(f"/staff/shipments/{shipment.id}/", {
            "status": Shipment.STATUS_TRANSIT,
            "estimated_delivery_date": "2026-06-08",
            "current_location": "Hetauda Hub Yard Checkpoint",
            "transit_note": "Linehaul convoy loaded and departed towards Hetauda Checkpoint."
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Retrieve and verify TransitLog
        log = TransitLog.objects.filter(shipment=shipment, status=Shipment.STATUS_TRANSIT).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.location, "Hetauda Hub Yard Checkpoint")
        self.assertEqual(log.description, "Linehaul convoy loaded and departed towards Hetauda Checkpoint.")
