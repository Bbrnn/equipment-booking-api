from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Organization Info', {'fields': ('role', 'department', 'phone_number')}),
    )