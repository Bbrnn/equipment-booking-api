from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from resources.models import Resource
from .models import Booking
from .serializers import BookingRejectSerializer, BookingSerializer
from .utils import get_available_quantity_for_range


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.select_related('user', 'reviewed_by').prefetch_related('items__resource')

        # Employees only see their own bookings; managers/admins see all
        if user.role == 'employee':
            queryset = queryset.filter(user=user)

        # Section F Filters: status, user, resource, start_date, end_date
        booking_status = self.request.query_params.get('status')
        if booking_status:
            queryset = queryset.filter(status=booking_status)

        user_id = self.request.query_params.get('user')
        if user_id and user.role in ['resource_manager', 'admin']:
            queryset = queryset.filter(user_id=user_id)

        resource_id = self.request.query_params.get('resource')
        if resource_id:
            queryset = queryset.filter(items__resource_id=resource_id).distinct()

        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.select_related('user', 'reviewed_by').prefetch_related('items__resource')
        if user.role == 'employee':
            return queryset.filter(user=user)
        return queryset


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only the booking owner (or admin) can cancel
        if booking.user != request.user and request.user.role != 'admin':
            return Response(
                {'detail': 'You can only cancel your own bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if booking.status not in ['pending', 'approved']:
            return Response(
                {'detail': f'Cannot cancel a booking with status "{booking.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.start_date <= timezone.now():
            return Response(
                {'detail': 'Cannot cancel a booking that has already started.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'cancelled'
        booking.save(update_fields=['status', 'updated_at'])
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class BookingApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        if request.user.role not in ['resource_manager', 'admin']:
            return Response(
                {'detail': 'Only resource managers or admins can approve bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            booking = Booking.objects.select_for_update().prefetch_related('items__resource').get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != 'pending':
            return Response(
                {'detail': f'Only pending bookings can be approved (current status: "{booking.status}").'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Re-check availability at approval time (handles competing pending requests like Employee C)
        for item in booking.items.all():
            if item.resource.status != 'active':
                return Response(
                    {'detail': f'Resource "{item.resource.name}" is no longer active.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            available = get_available_quantity_for_range(
                item.resource,
                booking.start_date,
                booking.end_date,
                exclude_booking_id=booking.id
            )
            if item.quantity > available:
                return Response(
                    {
                        'detail': (
                            f'Insufficient stock for "{item.resource.name}": '
                            f'only {available} available for these dates, but {item.quantity} requested.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        booking.status = 'approved'
        booking.reviewed_by = request.user
        booking.rejection_reason = ''
        booking.save(update_fields=['status', 'reviewed_by', 'rejection_reason', 'updated_at'])
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class BookingRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role not in ['resource_manager', 'admin']:
            return Response(
                {'detail': 'Only resource managers or admins can reject bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != 'pending':
            return Response(
                {'detail': f'Only pending bookings can be rejected (current status: "{booking.status}").'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking.status = 'rejected'
        booking.reviewed_by = request.user
        booking.rejection_reason = serializer.validated_data['rejection_reason']
        booking.save(update_fields=['status', 'reviewed_by', 'rejection_reason', 'updated_at'])
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class ResourceAvailabilityView(APIView):
    """
    Section E: Returns available active resources and remaining quantities
    for a given ?start_date=...&end_date=... range.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')

        if not start_str or not end_str:
            return Response(
                {'detail': 'Both start_date and end_date query parameters are required (ISO format).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = parse_datetime(start_str)
        end_date = parse_datetime(end_str)

        if not start_date or not end_date:
            return Response(
                {'detail': 'Invalid datetime format. Use ISO 8601, e.g. 2026-11-15T09:00:00Z.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if end_date <= start_date:
            return Response(
                {'detail': 'end_date must be after start_date.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        active_resources = Resource.objects.select_related('category').filter(status='active')
        results = []
        for resource in active_resources:
            available_qty = get_available_quantity_for_range(resource, start_date, end_date)
            results.append({
                'id': resource.id,
                'name': resource.name,
                'category': resource.category.name,
                'location': resource.location,
                'total_quantity': resource.total_quantity,
                'available_for_range': available_qty,
            })

        return Response(results, status=status.HTTP_200_OK)
