                                 
from django.contrib import admin
from .models import (
    Community, Dwelling, Tenant, RepairRequest,
    MaintenanceUpdate, Notification, UserProfile,
)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'population', 'created_at')
    search_fields = ('name', 'region')


@admin.register(Dwelling)
class DwellingAdmin(admin.ModelAdmin):
    list_display = ('address', 'community', 'structure_type',
                    'year_built', 'condition_score', 'is_occupied')
    list_filter = ('community', 'structure_type', 'is_occupied')
    search_fields = ('address',)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('user', 'dwelling', 'phone', 'lease_start', 'lease_end')


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'dwelling', 'priority', 'status',
                    'raised_by', 'assigned_to', 'created_at')
    list_filter = ('priority', 'status', 'category')
    search_fields = ('title', 'description')


@admin.register(MaintenanceUpdate)
class MaintenanceUpdateAdmin(admin.ModelAdmin):
    list_display = ('repair_request', 'author', 'status_change', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'community')
    list_filter = ('role',)
