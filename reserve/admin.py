from django.contrib import admin
from django.db.models import Q
from django.utils import timezone

from .models import DayReservation, Reservation


class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0

    fields = (
        "time",
        "user",
        "meeting_topic",
        "customer_name",
        "customer_email",
        "hold_expires_at",
    )

    readonly_fields = ("hold_expires_at",)
    ordering = ("time",)


@admin.register(DayReservation)
class DayReservationAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "total_reservations",
        "booked_reservations",
        "available_reservations",
    )

    list_filter = ("date",)
    ordering = ("date",)
    inlines = [ReservationInline]

    @admin.display(description="Total Slots")
    def total_reservations(self, obj):
        return obj.reservations.count()

    @admin.display(description="Booked")
    def booked_reservations(self, obj):
        return obj.reservations.filter(
            user__isnull=False,
        ).count()

    @admin.display(description="Available")
    def available_reservations(self, obj):
        now = timezone.now()

        return obj.reservations.filter(
            user__isnull=True,
        ).filter(
            Q(hold_expires_at__isnull=True)
            | Q(hold_expires_at__lte=now),
        ).count()


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "day",
        "time",
        "customer_name",
        "customer_email",
        "user",
        "reservation_status",
    )

    list_filter = (
        "day__date",
        "user",
    )

    search_fields = (
        "customer_name",
        "customer_email",
        "user__username",
        "user__email",
    )

    ordering = (
        "day__date",
        "time",
    )

    list_select_related = ("day", "user")

    fields = (
        "day",
        "time",
        "user",
        "customer_name",
        "customer_email",
        "meeting_topic",
        "hold_token",
        "hold_expires_at",
    )

    readonly_fields = (
        "hold_token",
        "hold_expires_at",
    )

    @admin.display(description="Status")
    def reservation_status(self, obj):
        if obj.user_id is not None:
            return "Booked"

        if (
            obj.hold_token is not None
            and obj.hold_expires_at is not None
            and obj.hold_expires_at > timezone.now()
        ):
            return "On Hold"

        return "Available"
