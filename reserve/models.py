from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class DayReservation(models.Model):
    date = models.DateField(_("Date"))

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return str(self.date)


class Reservation(models.Model):
    day = models.ForeignKey(
        DayReservation,
        on_delete=models.CASCADE,
        verbose_name=_("Day"),
        related_name="reservations",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("User"),
    )

    meeting_topic = models.TextField(
        blank=True,
        verbose_name=_("What would you like to cover?"),
    )

    hold_token = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
    )

    hold_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    time = models.TimeField(_("Time"))
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)

    class Meta:
        ordering = ("time",)
        constraints = [
            models.UniqueConstraint(
                fields=("day", "time"),
                name="unique_reservation_day_time",
            ),
        ]

    def __str__(self):
        return f"{self.day} - {self.time}"
