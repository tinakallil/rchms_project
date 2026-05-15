\
\
\
\
\
   
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


                                                                            
class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'System Administrator'
    HOUSING_OFFICER = 'HOUSING_OFFICER', 'Housing Officer'
    MAINTENANCE_SUPERVISOR = 'MAINTENANCE_SUPERVISOR', 'Maintenance Supervisor'
    TENANT = 'TENANT', 'Tenant'
    COMMUNITY_MANAGER = 'COMMUNITY_MANAGER', 'Community Manager'


class Community(models.Model):
                                                   
    name = models.CharField(max_length=120, unique=True)
    region = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    population = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Communities'

    def __str__(self):
        return f'{self.name} ({self.region})'


class Dwelling(models.Model):
                                                      
    class Structure(models.TextChoices):
        HOUSE = 'HOUSE', 'House'
        UNIT = 'UNIT', 'Unit'
        DUPLEX = 'DUPLEX', 'Duplex'

    community = models.ForeignKey(Community, on_delete=models.CASCADE,
                                  related_name='dwellings')
    address = models.CharField(max_length=255)
    structure_type = models.CharField(max_length=10, choices=Structure.choices)
    year_built = models.PositiveSmallIntegerField()
    condition_score = models.PositiveSmallIntegerField(
        default=5,
        help_text='1 (poor) to 10 (excellent).',
    )
    is_occupied = models.BooleanField(default=False)

    class Meta:
        ordering = ['community', 'address']

    def __str__(self):
        return f'{self.address} – {self.community.name}'


class Tenant(models.Model):
                                           
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='tenant_profile')
    dwelling = models.OneToOneField(Dwelling, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='tenant')
    phone = models.CharField(max_length=30, blank=True)
    lease_start = models.DateField(null=True, blank=True)
    lease_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class RepairRequest(models.Model):
                                                                      
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class Category(models.TextChoices):
        PLUMBING = 'PLUMBING', 'Plumbing'
        ELECTRICAL = 'ELECTRICAL', 'Electrical'
        STRUCTURAL = 'STRUCTURAL', 'Structural'
        APPLIANCE = 'APPLIANCE', 'Appliance'
        OTHER = 'OTHER', 'Other'

    dwelling = models.ForeignKey(Dwelling, on_delete=models.CASCADE,
                                 related_name='repair_requests')
    raised_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='raised_repairs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='assigned_repairs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices,
                                default=Category.OTHER)
    priority = models.CharField(max_length=10, choices=Priority.choices,
                                default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices,
                              default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} – {self.title} ({self.status})'

    @property
    def is_urgent(self):
        return self.priority == self.Priority.URGENT


class MaintenanceUpdate(models.Model):
                                                                     
    repair_request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE,
                                       related_name='updates')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                               related_name='maintenance_updates')
    note = models.TextField()
    status_change = models.CharField(
        max_length=15,
        choices=RepairRequest.Status.choices,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Update on #{self.repair_request_id} at {self.created_at:%Y-%m-%d}'


class UserProfile(models.Model):
                                                                   
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    role = models.CharField(max_length=30, choices=Role.choices,
                            default=Role.TENANT)
    community = models.ForeignKey(Community, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='staff')

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
                                                               
    if created:
        UserProfile.objects.create(user=instance)


class Notification(models.Model):
                                         
    recipient = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='notifications')
    repair_request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE,
                                       null=True, blank=True,
                                       related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'To {self.recipient.username}: {self.message[:40]}'
