from django.db import models
from django.conf import settings
from django.db.models import F,Q

#Cateory model to categorize resources
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

#Resource model to represent equipment or resources available for booking
class Resource(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        'Category', 
        on_delete=models.PROTECT, 
        related_name='resources'
        )  # Using PROTECT prevents accidentally deleting a category that still has active equipment.
    total_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_resources'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(
                check=Q(available_quantity__lte=F('total_quantity')),
                name='available_quantity_lte_total_quantity'
            ),
        ]
                                                    
    
    def __str__(self):
        return self.name
    
