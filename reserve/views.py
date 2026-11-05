import uuid
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reservation
from .serializers import ReservationSerializer

from utils.turn_maker import create_reservations

HOLD_DURATION = timedelta(minutes=10)

def home(request):
    return render(request, "reserve/index.html")


def booking(request):
    return render(request, "reserve/booking.html")


def hold_session_key(reservation_id):
    return f"reservation_hold_{reservation_id}"


class BookingHoldView(APIView):
    """
    Temporarily holds a reservation for the current browser session.
    Login is not required to create a hold.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        reservation_id = request.data.get("reservation_id")

        if not reservation_id:
            return Response(
                {"error": "reservation_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reservation_id = int(reservation_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid reservation_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        expires_at = now + HOLD_DURATION
        session_key = hold_session_key(reservation_id)

        # Reuse an existing valid hold owned by this session.
        existing_token = request.session.get(session_key)

        if existing_token:
            try:
                existing_token = uuid.UUID(existing_token)
            except (TypeError, ValueError, AttributeError):
                existing_token = None

            if existing_token:
                existing_hold = Reservation.objects.filter(
                    pk=reservation_id,
                    user__isnull=True,
                    hold_token=existing_token,
                    hold_expires_at__gt=now,
                ).first()

                if existing_hold:
                    return Response(
                        {
                            "message": "Reservation hold is active.",
                            "reservation_id": existing_hold.pk,
                            "expires_at": existing_hold.hold_expires_at,
                        },
                        status=status.HTTP_200_OK,
                    )

        token = uuid.uuid4()

        # Conditional UPDATE ensures that only one request can claim
        # an available slot whose previous hold has expired.
        updated = Reservation.objects.filter(
            pk=reservation_id,
            user__isnull=True,
        ).filter(
            Q(hold_expires_at__isnull=True)
            | Q(hold_expires_at__lte=now)
        ).update(
            hold_token=token,
            hold_expires_at=expires_at,
        )

        if updated != 1:
            exists = Reservation.objects.filter(
                pk=reservation_id
            ).exists()

            if not exists:
                return Response(
                    {"error": "Reservation not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "error": (
                        "This reservation is booked or currently "
                        "held by another user."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        request.session[session_key] = str(token)

        return Response(
            {
                "message": "Reservation held successfully.",
                "reservation_id": reservation_id,
                "expires_at": expires_at,
            },
            status=status.HTTP_200_OK,
        )


class BookingReleaseView(APIView):
    """
    Releases a hold owned by the current browser session.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        reservation_id = request.data.get("reservation_id")

        if not reservation_id:
            return Response(
                {"error": "reservation_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reservation_id = int(reservation_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid reservation_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_key = hold_session_key(reservation_id)
        token = request.session.get(session_key)

        if token:
            try:
                token = uuid.UUID(token)
            except (TypeError, ValueError, AttributeError):
                token = None

        if token:
            Reservation.objects.filter(
                pk=reservation_id,
                user__isnull=True,
                hold_token=token,
            ).update(
                hold_token=None,
                hold_expires_at=None,
            )

        request.session.pop(session_key, None)

        return Response(
            {"message": "Hold released if it belonged to this session."},
            status=status.HTTP_200_OK,
        )


class BookingView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request):
        now = timezone.now()
        # Show only available reservations by default.
        available_filter = (
            Q(user__isnull=True)
            & (
                Q(hold_expires_at__isnull=True)
                | Q(hold_expires_at__lte=now)
            )
        )

        # Include active holds belonging to this browser session.
        # This allows the selected reservation to be restored after login.
        own_holds = []

        for key, value in request.session.items():
            if not key.startswith("reservation_hold_"):
                continue

            try:
                reservation_id = int(
                    key.removeprefix("reservation_hold_")
                )
                token = uuid.UUID(value)
            except (TypeError, ValueError, AttributeError):
                continue

            own_holds.append(
                Q(
                    pk=reservation_id,
                    user__isnull=True,
                    hold_token=token,
                    hold_expires_at__gt=now,
                )
            )

        own_holds_filter = Q(pk__in=[])

        for own_hold in own_holds:
            own_holds_filter |= own_hold

        reservations = Reservation.objects.filter(
            available_filter | own_holds_filter
        ).select_related("day").order_by(
            "day__date",
            "time",
        )

        serializer = ReservationSerializer(reservations, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        reservation_id = request.data.get("reservation_id")

        if not reservation_id:
            return Response(
                {"error": "reservation_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reservation_id = int(reservation_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid reservation_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_key = hold_session_key(reservation_id)
        token = request.session.get(session_key)

        if not token:
            return Response(
                {
                    "error": (
                        "Your reservation hold was not found. "
                        "Please select the time again."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            token = uuid.UUID(token)
        except (TypeError, ValueError, AttributeError):
            request.session.pop(session_key, None)

            return Response(
                {"error": "Invalid reservation hold. Please select again."},
                status=status.HTTP_409_CONFLICT,
            )

        now = timezone.now()

        customer_name = str(
            request.data.get("customer_name", "")
        ).strip()

        customer_email = str(
            request.data.get("customer_email", "")
        ).strip()

        meeting_topic = str(
            request.data.get("meeting_topic", "")
        ).strip()

        if not customer_name or not customer_email:
            return Response(
                {"error": "Name and email are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Atomically confirm the reservation only if this session
        # still owns a valid hold.
        updated = Reservation.objects.filter(
            pk=reservation_id,
            user__isnull=True,
            hold_token=token,
            hold_expires_at__gt=now,
        ).update(
            user=request.user,
            customer_name=customer_name,
            customer_email=customer_email,
            meeting_topic=meeting_topic,
            hold_token=None,
            hold_expires_at=None,
        )

        if updated != 1:
            request.session.pop(session_key, None)

            return Response(
                {
                    "error": (
                        "Your reservation hold expired or the slot is "
                        "no longer available. Please select another time."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        request.session.pop(session_key, None)

        reservation = Reservation.objects.select_related("day").get(
            pk=reservation_id
        )

        return Response(
            {
                "message": "Reservation booked successfully.",
                "reservation": ReservationSerializer(reservation).data,
            },
            status=status.HTTP_200_OK,
        )


class MyBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_bookings = Reservation.objects.filter(
            user=request.user
        ).select_related("day").order_by(
            "day__date",
            "time",
        )

        serialized_data = ReservationSerializer(
            user_bookings,
            many=True,
        ).data

        return Response(
            serialized_data,
            status=status.HTTP_200_OK,
        )


class CancelBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, reservation_id):
        with transaction.atomic():
            reservation = Reservation.objects.select_for_update().filter(
                id=reservation_id,
                user=request.user,
            ).first()

            if reservation is None:
                return Response(
                    {"error": "Reservation not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            reservation.user = None
            reservation.customer_name = ""
            reservation.customer_email = ""
            reservation.meeting_topic = ""
            reservation.hold_token = None
            reservation.hold_expires_at = None

            reservation.save(
                update_fields=[
                    "user",
                    "customer_name",
                    "customer_email",
                    "meeting_topic",
                    "hold_token",
                    "hold_expires_at",
                ]
            )

        return Response(
            {"message": "Reservation cancelled successfully."},
            status=status.HTTP_200_OK,
        )


@login_required(login_url="account:login")
def my_bookings_page(request):
    return render(request, "reserve/my_bookings.html")
