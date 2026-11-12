from django.db.models import Sum
from .models import BookingItem


def get_available_quantity_for_range(resource, start_date, end_date, exclude_booking_id=None):
    """
    Calculates how many units of a resource are available between start_date and end_date,
    accounting only for existing APPROVED bookings that overlap the requested period.
    """
    if resource.status != 'active':
        return 0

    overlapping_items = BookingItem.objects.filter(
        resource=resource,
        booking__status='approved',
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date,
    )

    if exclude_booking_id:
        overlapping_items = overlapping_items.exclude(booking_id=exclude_booking_id)

    reserved_qty = overlapping_items.aggregate(total=Sum('quantity'))['total'] or 0
    return max(resource.total_quantity - reserved_qty, 0)
