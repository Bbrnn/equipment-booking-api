from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Category, Resource
from .permissions import IsResourceManagerOrAdminOrReadOnly
from .serializers import CategorySerializer, ResourceSerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsResourceManagerOrAdminOrReadOnly]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsResourceManagerOrAdminOrReadOnly]


class ResourceListCreateView(generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [IsResourceManagerOrAdminOrReadOnly]

    def get_queryset(self):
        queryset = Resource.objects.select_related('category', 'managed_by').all()

        # Regular employees only see active resources unless they are managers/admins
        if self.request.user.role == 'employee':
            queryset = queryset.filter(status='active')

        # 1. Filter by category ID (?category=1)
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # 2. Filter by location (?location=Nairobi)
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)

        # 3. Filter by availability (?available=true or ?available=false)
        available = self.request.query_params.get('available')
        if available is not None:
            if available.lower() == 'true':
                queryset = queryset.filter(status='active', available_quantity__gt=0)
            elif available.lower() == 'false':
                queryset = queryset.filter(Q(status='inactive') | Q(available_quantity=0))

        # 4. Filter by status explicitly (?status=active or ?status=inactive)
        resource_status = self.request.query_params.get('status')
        if resource_status:
            queryset = queryset.filter(status=resource_status)

        # 5. Search by keyword in name or description (?search=projector)
        keyword = self.request.query_params.get('search')
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) | Q(description__icontains=keyword)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(managed_by=self.request.user)


class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resource.objects.select_related('category', 'managed_by').all()
    serializer_class = ResourceSerializer
    permission_classes = [IsResourceManagerOrAdminOrReadOnly]
