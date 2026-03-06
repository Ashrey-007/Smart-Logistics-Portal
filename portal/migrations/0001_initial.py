from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone_number", models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(message="Enter a valid phone number.", regex="^[0-9+\\-\\s]{7,20}$")])),
                ("address", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="customer", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_name", models.CharField(max_length=120)),
                ("phone_number", models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(message="Enter a valid phone number.", regex="^[0-9+\\-\\s]{7,20}$")])),
                ("email", models.EmailField(max_length=254)),
                ("cargo_type", models.CharField(max_length=100)),
                ("weight", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.1)])),
                ("pickup_location", models.CharField(max_length=180)),
                ("destination", models.CharField(max_length=180)),
                ("pickup_date", models.DateField()),
                ("additional_notes", models.TextField(blank=True)),
                ("booking_status", models.CharField(choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")], default="Pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookings", to="portal.customer")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tracking_id", models.CharField(max_length=30)),
                ("complaint_type", models.CharField(choices=[("Delivery Delay", "Delivery Delay"), ("Cargo Damage", "Cargo Damage"), ("Billing Issue", "Billing Issue"), ("Service Issue", "Service Issue"), ("Other", "Other")], max_length=40)),
                ("message", models.TextField()),
                ("complaint_status", models.CharField(choices=[("Open", "Open"), ("Under Review", "Under Review"), ("Resolved", "Resolved")], default="Open", max_length=30)),
                ("admin_reply", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="complaints", to="portal.customer")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tracking_id", models.CharField(editable=False, max_length=30, unique=True)),
                ("status", models.CharField(choices=[("Pending", "Pending"), ("Received", "Received"), ("In Warehouse", "In Warehouse"), ("Customs Cleared", "Customs Cleared"), ("In Transit", "In Transit"), ("Delivered", "Delivered")], default="Pending", max_length=30)),
                ("estimated_delivery_date", models.DateField()),
                ("current_location", models.CharField(blank=True, max_length=180)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="shipment", to="portal.booking")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
