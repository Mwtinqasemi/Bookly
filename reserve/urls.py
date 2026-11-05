from django.urls import path

from .views import (
    BookingHoldView,
    BookingReleaseView,
    BookingView,
    CancelBookingView,
    MyBookingsView,
    booking,
    home,
    my_bookings_page,
)


app_name = "reserve"

urlpatterns = [
    path(
        "",
        home,
        name="home",
    ),
    path(
        "booking/",
        booking,
        name="booking-form",
    ),
    path(
        "my-bookings/",
        my_bookings_page,
        name="my_bookings_page",
    ),
    path(
        "api/booking/",
        BookingView.as_view(),
        name="booking",
    ),
    path(
        "api/booking/hold/",
        BookingHoldView.as_view(),
        name="hold",
    ),
    path(
        "api/booking/release/",
        BookingReleaseView.as_view(),
        name="release",
    ),
    path(
        "api/my-bookings/",
        MyBookingsView.as_view(),
        name="my-bookings",
    ),
    path(
        "api/my-bookings/<int:reservation_id>/",
        CancelBookingView.as_view(),
        name="delete-booking",
    ),
]
