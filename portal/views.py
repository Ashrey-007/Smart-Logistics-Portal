from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    BookingForm,
    BookingStatusForm,
    ComplaintForm,
    ComplaintReplyForm,
    CustomerRegistrationForm,
    ShipmentStatusForm,
    TrackingSearchForm,
)
from .models import Booking, Complaint, Customer, Shipment


def staff_required(user):
    return user.is_authenticated and user.is_staff


def home(request):
    return render(request, "portal/home.html")


def about(request):
    return render(request, "portal/about.html")


def contact(request):
    return render(request, "portal/contact.html")


def register(request):
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Customer account created.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    customer = get_object_or_404(Customer, user=request.user)
    bookings = Booking.objects.filter(customer=customer)
    shipments = Shipment.objects.filter(booking__customer=customer)
    complaints = Complaint.objects.filter(customer=customer)
    return render(
        request,
        "portal/dashboard.html",
        {
            "booking_count": bookings.count(),
            "shipment_count": shipments.count(),
            "complaint_count": complaints.count(),
            "latest_shipments": shipments[:6],
            "recent_bookings": bookings[:6],
        },
    )


@login_required
def create_booking(request):
    customer = get_object_or_404(Customer, user=request.user)
    initial = {"customer_name": str(customer), "phone_number": customer.phone_number, "email": request.user.email}
    form = BookingForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.customer = customer
        
        # Dynamic pricing formula
        vol_weight = (booking.length * booking.width * booking.height) / 5000
        billable_weight = max(float(booking.weight), float(vol_weight))
        
        base_cost = billable_weight * 1.50
        service_multipliers = {
            "Standard": 1.0,
            "Express": 1.5,
            "Priority": 2.5
        }
        multiplier = service_multipliers.get(booking.service_level, 1.0)
        value_surcharge = float(booking.declared_value) * 0.015
        
        booking.estimated_cost = base_cost * multiplier + value_surcharge
        booking.save()
        messages.success(request, f"Booking request submitted. Estimated Freight Charge: NPR {booking.estimated_cost:,.2f}")
        return redirect("booking_history")
    return render(request, "portal/booking_form.html", {"form": form})


def track_shipment(request):
    form = TrackingSearchForm(request.GET or None)
    shipment = None
    searched = False
    milestones = []
    if form.is_valid():
        searched = True
        shipment = Shipment.objects.filter(tracking_id__iexact=form.cleaned_data["tracking_id"].strip()).first()
        if shipment:
            milestones = shipment.milestones.all().order_by("timestamp")
        else:
            messages.warning(request, "No shipment found for that tracking ID.")
    return render(request, "portal/tracking.html", {
        "form": form,
        "shipment": shipment,
        "searched": searched,
        "milestones": milestones
    })


@login_required
def create_complaint(request):
    customer = get_object_or_404(Customer, user=request.user)
    form = ComplaintForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        complaint = form.save(commit=False)
        complaint.customer = customer
        complaint.save()
        messages.success(request, "Complaint submitted to customer success.")
        return redirect("create_complaint")
    return render(request, "portal/complaint_form.html", {"form": form, "complaints": Complaint.objects.filter(customer=customer)})


@login_required
def booking_history(request):
    customer = get_object_or_404(Customer, user=request.user)
    status = request.GET.get("status", "")
    bookings = Booking.objects.filter(customer=customer)
    if status:
        bookings = bookings.filter(booking_status=status)
    return render(request, "portal/booking_history.html", {"bookings": bookings, "status": status, "status_choices": Booking.STATUS_CHOICES})


@user_passes_test(staff_required)
def admin_dashboard(request):
    booking_status = request.GET.get("booking_status", "")
    shipment_status = request.GET.get("shipment_status", "")
    search = request.GET.get("q", "")
    bookings = Booking.objects.select_related("customer__user")
    shipments = Shipment.objects.select_related("booking")
    complaints = Complaint.objects.select_related("customer__user")
    if booking_status:
        bookings = bookings.filter(booking_status=booking_status)
    if shipment_status:
        shipments = shipments.filter(status=shipment_status)
    if search:
        bookings = bookings.filter(customer_name__icontains=search)
        shipments = shipments.filter(tracking_id__icontains=search)
        complaints = complaints.filter(tracking_id__icontains=search)
    chart = Shipment.objects.values("status").annotate(total=Count("id")).order_by("status")
    
    from django.db.models import Sum
    total_revenue = Booking.objects.filter(booking_status=Booking.STATUS_APPROVED).aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or 0.0

    return render(
        request,
        "portal/admin_dashboard.html",
        {
            "total_bookings": Booking.objects.count(),
            "total_shipments": Shipment.objects.count(),
            "total_complaints": Complaint.objects.count(),
            "total_customers": Customer.objects.count(),
            "pending_bookings": Booking.objects.filter(booking_status=Booking.STATUS_PENDING).count(),
            "open_complaints": Complaint.objects.filter(complaint_status=Complaint.STATUS_OPEN).count(),
            "total_revenue": total_revenue,
            "bookings": bookings[:10],
            "shipments": shipments[:10],
            "complaints": complaints[:10],
            "customers": User.objects.filter(is_staff=False).select_related("customer")[:10],
            "booking_status": booking_status,
            "shipment_status": shipment_status,
            "search": search,
            "booking_status_choices": Booking.STATUS_CHOICES,
            "shipment_status_choices": Shipment.STATUS_CHOICES,
            "chart_labels": [row["status"] for row in chart],
            "chart_values": [row["total"] for row in chart],
        },
    )


@user_passes_test(staff_required)
def admin_booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    form = BookingStatusForm(request.POST or None, instance=booking)
    if request.method == "POST" and form.is_valid():
        booking = form.save()
        if booking.booking_status == Booking.STATUS_APPROVED:
            shipment, created = Shipment.objects.get_or_create(
                booking=booking,
                defaults={"estimated_delivery_date": booking.pickup_date + timedelta(days=7), "current_location": booking.pickup_location},
            )
            if created:
                from .models import TransitLog
                TransitLog.objects.create(
                    shipment=shipment,
                    location=shipment.current_location,
                    status=shipment.status,
                    description=f"Shipment booking approved. Freight created at {shipment.current_location} origin and queued for dispatch."
                )
        messages.success(request, "Booking decision saved.")
        return redirect("admin_dashboard")
    return render(request, "portal/admin_booking_detail.html", {"booking": booking, "form": form})


@user_passes_test(staff_required)
def admin_shipment_update(request, shipment_id):
    shipment = get_object_or_404(Shipment, id=shipment_id)
    form = ShipmentStatusForm(request.POST or None, instance=shipment)
    if request.method == "POST" and form.is_valid():
        shipment = form.save()
        transit_note = form.cleaned_data.get("transit_note", "")
        
        from .models import TransitLog
        TransitLog.objects.create(
            shipment=shipment,
            location=shipment.current_location,
            status=shipment.status,
            description=transit_note or f"Shipment status updated to {shipment.get_status_display()} at {shipment.current_location}."
        )
        
        messages.success(request, "Shipment milestone updated.")
        return redirect("admin_dashboard")
    return render(request, "portal/admin_shipment_update.html", {"shipment": shipment, "form": form})


@user_passes_test(staff_required)
def admin_complaint_reply(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    form = ComplaintReplyForm(request.POST or None, instance=complaint)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Complaint response saved.")
        return redirect("admin_dashboard")
    return render(request, "portal/admin_complaint_reply.html", {"complaint": complaint, "form": form})
