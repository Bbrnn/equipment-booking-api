from django.db import transaction
from rest_framework import serializers
from .models import Booking, BookingItem
from .utils import get_available_quantity_for_range


class BookingItemSerializer(serializers.ModelSerializer):
    resource_name = serializers.ReadOnlyField(source='resource.name')

    class Meta:
        model = BookingItem
        fields = ['id', 'resource', 'resource_name', 'quantity']
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True)
    user_username = serializers.ReadOnlyField(source='user.username')
    reviewed_by_username = serializers.ReadOnlyField(source='reviewed_by.username')

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_username',
            'start_date',
            'end_date',
            'purpose',
            'status',
            'reviewed_by',
            'reviewed_by_username',
            'rejection_reason',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'reviewed_by',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        items = attrs.get('items', [])

        if end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })

        if not items:
            raise serializers.ValidationError({
                'items': 'At least one resource item must be included in a booking.'
            })

        seen_resources = set()
        for item in items:
            resource = item['resource']
            qty = item['quantity']

            if resource.id in seen_resources:
                raise serializers.ValidationError({
                    'items': f'Duplicate resource "{resource.name}" in the same booking request.'
                })
            seen_resources.add(resource.id)

            if resource.status != 'active':
                raise serializers.ValidationError({
                    'items': f'Resource "{resource.name}" is inactive and cannot be booked.'
                })

            available = get_available_quantity_for_range(resource, start_date, end_date)
            if qty > available:
                raise serializers.ValidationError({
                    'items': (
                        f'Only {available} unit(s) of "{resource.name}" are available '
                        f'for the selected dates (requested {qty}).'
                    )
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        booking = Booking.objects.create(**validated_data)
        for item_data in items_data:
            BookingItem.objects.create(booking=booking, **item_data)
        return booking


class BookingRejectSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True, allow_blank=False)
