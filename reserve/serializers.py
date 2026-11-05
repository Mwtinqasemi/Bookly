from rest_framework import serializers

from .models import DayReservation, Reservation


class DayReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayReservation
        fields = "__all__"


class ReservationSerializer(serializers.ModelSerializer):
    day = DayReservationSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "day",
            "time",
            "customer_name",
            "customer_email",
            "meeting_topic",
        ]
