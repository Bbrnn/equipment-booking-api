from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from resources.models import Category, Resource
from .models import Booking

User = get_user_model()


class BookingWorkflowTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager1@example.com',
            password='Password123!',
            role='resource_manager'
        )
        self.employee_a = User.objects.create_user(
            username='emp_a',
            email='empa@example.com',
            password='Password123!',
            role='employee'
        )
        self.employee_b = User.objects.create_user(
            username='emp_b',
            email='empb@example.com',
            password='Password123!',
            role='employee'
        )
        self.category = Category.objects.create(name='Projectors')
        self.projector = Resource.objects.create(
            name='Epson Projector',
            category=self.category,
            total_quantity=5,
            available_quantity=5,
            status='active',
            managed_by=self.manager
        )
        self.start = timezone.now() + timedelta(days=2)
        self.end = timezone.now() + timedelta(days=4)

    def test_projector_overlap_prevents_overbooking(self):
        # Employee A books 2 projectors
        self.client.force_authenticate(user=self.employee_a)
        res1 = self.client.post('/api/bookings/', {
            'start_date': self.start.isoformat(),
            'end_date': self.end.isoformat(),
            'purpose': 'Workshop A',
            'items': [{'resource': self.projector.id, 'quantity': 2}]
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        booking_a_id = res1.data['id']

        # Manager approves Booking A
        self.client.force_authenticate(user=self.manager)
        approve_a = self.client.post(f'/api/bookings/{booking_a_id}/approve/')
        self.assertEqual(approve_a.status_code, status.HTTP_200_OK)

        # Employee B tries to book 4 projectors during the same window (only 3 left)
        self.client.force_authenticate(user=self.employee_b)
        res2 = self.client.post('/api/bookings/', {
            'start_date': self.start.isoformat(),
            'end_date': self.end.isoformat(),
            'purpose': 'Workshop B',
            'items': [{'resource': self.projector.id, 'quantity': 4}]
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

