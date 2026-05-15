                                                

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Community',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('region', models.CharField(max_length=120)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('population', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Communities',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Dwelling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=255)),
                ('structure_type', models.CharField(choices=[('HOUSE', 'House'), ('UNIT', 'Unit'), ('DUPLEX', 'Duplex')], max_length=10)),
                ('year_built', models.PositiveSmallIntegerField()),
                ('condition_score', models.PositiveSmallIntegerField(default=5, help_text='1 (poor) to 10 (excellent).')),
                ('is_occupied', models.BooleanField(default=False)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dwellings', to='housing.community')),
            ],
            options={
                'ordering': ['community', 'address'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'System Administrator'), ('HOUSING_OFFICER', 'Housing Officer'), ('MAINTENANCE_SUPERVISOR', 'Maintenance Supervisor'), ('TENANT', 'Tenant'), ('COMMUNITY_MANAGER', 'Community Manager')], default='TENANT', max_length=30)),
                ('community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staff', to='housing.community')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('lease_start', models.DateField(blank=True, null=True)),
                ('lease_end', models.DateField(blank=True, null=True)),
                ('dwelling', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tenant', to='housing.dwelling')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RepairRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('PLUMBING', 'Plumbing'), ('ELECTRICAL', 'Electrical'), ('STRUCTURAL', 'Structural'), ('APPLIANCE', 'Appliance'), ('OTHER', 'Other')], default='OTHER', max_length=20)),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')], default='MEDIUM', max_length=10)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('ASSIGNED', 'Assigned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='OPEN', max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_repairs', to=settings.AUTH_USER_MODEL)),
                ('dwelling', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repair_requests', to='housing.dwelling')),
                ('raised_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='raised_repairs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('repair_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='housing.repairrequest')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('status_change', models.CharField(blank=True, choices=[('OPEN', 'Open'), ('ASSIGNED', 'Assigned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='maintenance_updates', to=settings.AUTH_USER_MODEL)),
                ('repair_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='housing.repairrequest')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
