from django.urls import path
from .views import (
    BookingApproveView,
    BookingCancelView,
    BookingDetailView,
    BookingListCreateView,
    BookingRejectView,
    ResourceAvailabilityView,
)

urlpatterns = [
    path('', BookingListCreateView.as_view(), name='booking-list-create'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('<int:pk>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path('<int:pk>/approve/', BookingApproveView.as_view(), name='booking-approve'),
    path('<int:pk>/reject/', BookingRejectView.as_view(), name='booking-reject'),
    path('availability/', ResourceAvailabilityView.as_view(), name='resource-availability'),
]
