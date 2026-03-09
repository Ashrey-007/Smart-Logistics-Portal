from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking, Complaint, Customer, Shipment


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"


class CustomerRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=80)
    last_name = forms.CharField(max_length=80)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone_number", "address", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Customer.objects.create(
                user=user,
                phone_number=self.cleaned_data["phone_number"],
                address=self.cleaned_data.get("address", ""),
            )
        return user


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class BookingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Booking
        exclude = ["customer", "booking_status", "estimated_cost"]
        widgets = {
            "pickup_date": forms.DateInput(attrs={"type": "date"}),
            "additional_notes": forms.Textarea(attrs={"rows": 4}),
            "length": forms.NumberInput(attrs={"placeholder": "Length in cm"}),
            "width": forms.NumberInput(attrs={"placeholder": "Width in cm"}),
            "height": forms.NumberInput(attrs={"placeholder": "Height in cm"}),
            "declared_value": forms.NumberInput(attrs={"placeholder": "Declared cargo value"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_pickup_date(self):
        pickup_date = self.cleaned_data["pickup_date"]
        if pickup_date < timezone.localdate():
            raise forms.ValidationError("Pickup date cannot be in the past.")
        return pickup_date


class TrackingSearchForm(BootstrapFormMixin, forms.Form):
    tracking_id = forms.CharField(max_length=30)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
        self.fields["tracking_id"].widget.attrs["placeholder"] = "SL-XXXXXXXXXX"


class ComplaintForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["tracking_id", "complaint_type", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class BookingStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ShipmentStatusForm(BootstrapFormMixin, forms.ModelForm):
    transit_note = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., Arrived at Hetauda Hub Yard"}),
        label="Transit Milestones Note"
    )

    class Meta:
        model = Shipment
        fields = ["status", "estimated_delivery_date", "current_location"]
        widgets = {"estimated_delivery_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ComplaintReplyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["complaint_status", "admin_reply"]
        widgets = {"admin_reply": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
