from django.contrib import admin
from .models import Category, Resource

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'created_at')
    search_fields = ('name',)

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'category', 'total_quantity', 'available_quantity', 'location', 'status', )
    list_filter = ('category', 'status', 'location')
    search_fields = ('name', 'description', 'managed_by__username')

