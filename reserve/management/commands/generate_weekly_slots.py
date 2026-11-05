from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from reserve.models import DayReservation, Reservation

from django.utils import timezone

class Command(BaseCommand):
    help = "Generate reservation slots for the upcoming workweek."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=30,
            help="Interval between reservation slots in minutes.",
        )

    def handle(self, *args, **options):
        interval = options["interval"]

        if interval <= 0:
            self.stderr.write(
                self.style.ERROR("Interval must be greater than zero.")
            )
            return

        today = timezone.localdate()

        days_until_monday = (7 - today.weekday()) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        next_monday = today + timedelta(days=days_until_monday)
        created_days = 0
        created_slots = 0

        with transaction.atomic():
            for day_offset in range(5):
                reservation_date = next_monday + timedelta(
                    days=day_offset
                )

                day, day_created = DayReservation.objects.get_or_create(
                    date=reservation_date
                )

                if day_created:
                    created_days += 1

                time_ranges = [
                    (time(9, 0), time(13, 0)),
                    (time(17, 0), time(22, 0)),
                ]

                for start_time, end_time in time_ranges:
                    current_time = start_time

                    while current_time < end_time:
                        _, slot_created = Reservation.objects.get_or_create(
                            day=day,
                            time=current_time,
                        )

                        if slot_created:
                            created_slots += 1

                        current_time = (
                            datetime.combine(date.min, current_time)
                            + timedelta(minutes=interval)
                        ).time()

        self.stdout.write(
            self.style.SUCCESS(
                f"Weekly slots generated successfully. "
                f"Week: {next_monday} to "
                f"{next_monday + timedelta(days=4)}. "
                f"New days: {created_days}. "
                f"New slots: {created_slots}."
            )
        )