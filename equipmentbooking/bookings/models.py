from django.conf import settings


from django.db import models

from django.db.models import F, Q
from resources.models import Resource
# Create your models here. 
# Booking model to represent a booking of a resource
# BookingItem model to represent individual items within a booking

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    purpose = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_bookings'
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=Q(end_date__gt=F('start_date')),
                name='end_date_after_start_date'
            ),
        ]


    def __str__(self):
        return f"Booking #{self.id} by {self.user.username} from {self.status}"


class BookingItem(models.Model):
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    resource = models.ForeignKey(
        Resource, 
        on_delete=models.PROTECT, 
        related_name='booking_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'resource'],
                name='unique_booking_resource'
            ),
            models.CheckConstraint(
                check=Q(quantity__gte=1),
                name='booking_item_quantity_gte_1'
            ),
        ]

      

    def __str__(self):
        return f"{self.quantity} x {self.resource.name} for Booking #{self.booking.id}"