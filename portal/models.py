import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(r"^[0-9+\-\s]{7,20}$", "Enter a valid phone number.")


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer")
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Booking(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_REJECTED = "Rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="bookings")
    customer_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField()
    cargo_type = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.1)])
    pickup_location = models.CharField(max_length=180)
    destination = models.CharField(max_length=180)
    pickup_date = models.DateField()
    additional_notes = models.TextField(blank=True)
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    length = models.DecimalField(max_digits=6, decimal_places=2, default=10.0) # in cm
    width = models.DecimalField(max_digits=6, decimal_places=2, default=10.0)  # in cm
    height = models.DecimalField(max_digits=6, decimal_places=2, default=10.0) # in cm
    service_level = models.CharField(
        max_length=30,
        choices=[
            ("Standard", "Standard (Economy)"),
            ("Express", "Express Road (Fast)"),
            ("Priority", "Priority Air (Next-Day)"),
        ],
        default="Standard",
    )
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_name} to {self.destination}"


class Shipment(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_RECEIVED = "Received"
    STATUS_WAREHOUSE = "In Warehouse"
    STATUS_CUSTOMS = "Customs Cleared"
    STATUS_TRANSIT = "In Transit"
    STATUS_DELIVERED = "Delivered"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_WAREHOUSE, "In Warehouse"),
        (STATUS_CUSTOMS, "Customs Cleared"),
        (STATUS_TRANSIT, "In Transit"),
        (STATUS_DELIVERED, "Delivered"),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="shipment")
    tracking_id = models.CharField(max_length=30, unique=True, editable=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    estimated_delivery_date = models.DateField()
    current_location = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = f"SL-{uuid.uuid4().hex[:10].upper()}"
        if not self.estimated_delivery_date:
            self.estimated_delivery_date = timezone.localdate() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def progress_percent(self):
        statuses = [status for status, _ in self.STATUS_CHOICES]
        return int((statuses.index(self.status) + 1) / len(statuses) * 100)

    def __str__(self):
        return self.tracking_id


class Complaint(models.Model):
    STATUS_OPEN = "Open"
    STATUS_REVIEW = "Under Review"
    STATUS_RESOLVED = "Resolved"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_REVIEW, "Under Review"),
        (STATUS_RESOLVED, "Resolved"),
    ]
    TYPE_CHOICES = [
        ("Delivery Delay", "Delivery Delay"),
        ("Cargo Damage", "Cargo Damage"),
        ("Billing Issue", "Billing Issue"),
        ("Service Issue", "Service Issue"),
        ("Other", "Other"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="complaints")
    tracking_id = models.CharField(max_length=30)
    complaint_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    message = models.TextField()
    complaint_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)
    admin_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_id} - {self.complaint_type}"


class TransitLog(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="milestones")
    location = models.CharField(max_length=180)
    status = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.shipment.tracking_id} - {self.location} ({self.status})"
