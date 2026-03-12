from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("booking/new/", views.create_booking, name="create_booking"),
    path("tracking/", views.track_shipment, name="track_shipment"),
    path("complaints/new/", views.create_complaint, name="create_complaint"),
    path("history/", views.booking_history, name="booking_history"),
    path("staff/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("staff/bookings/<int:booking_id>/", views.admin_booking_detail, name="admin_booking_detail"),
    path("staff/shipments/<int:shipment_id>/", views.admin_shipment_update, name="admin_shipment_update"),
    path("staff/complaints/<int:complaint_id>/", views.admin_complaint_reply, name="admin_complaint_reply"),
]
