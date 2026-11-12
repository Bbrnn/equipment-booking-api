from rest_framework import serializers
from .models import Resource, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class ResourceSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    managed_by_username = serializers.ReadOnlyField(source='managed_by.username')

    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'total_quantity', 'available_quantity', 'location',
            'status', 'managed_by', 'managed_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'managed_by', 'created_at', 'updated_at']

    def validate(self, attrs):

        #Fall back to existing instance values during updates if not provided in the request(PATCH requests)
        total_qty = attrs.get(
            'total_quantity', 
            self.instance.total_quantity if self.instance else 1
        )

        available_qty = attrs.get(
            'available_quantity', 
            self.instance.available_quantity if self.instance else total_qty
        )
        
        if available_qty > total_qty:
            raise serializers.ValidationError({
                'available_quantity': 'Available quantity cannot exceed total quantity.'

            }
        )
        return attrs