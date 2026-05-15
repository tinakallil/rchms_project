
   
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from housing.models import (
    Community, Dwelling, RepairRequest, Role,
)


class Command(BaseCommand):
    help = 'Populate the database with demo communities, dwellings, users and requests.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding RCHMS demo data...')

                        
        c1, _ = Community.objects.get_or_create(
            name='Yuendumu', defaults={'region': 'NT', 'population': 800})
        c2, _ = Community.objects.get_or_create(
            name='Maningrida', defaults={'region': 'NT', 'population': 2300})

                      
        d1, _ = Dwelling.objects.get_or_create(
            community=c1, address='12 Acacia St',
            defaults={'structure_type': 'HOUSE', 'year_built': 2012, 'condition_score': 7})
        d2, _ = Dwelling.objects.get_or_create(
            community=c1, address='5 Bauhinia Rd',
            defaults={'structure_type': 'UNIT', 'year_built': 2018, 'condition_score': 9})
        d3, _ = Dwelling.objects.get_or_create(
            community=c2, address='3 Eucalyptus Cl',
            defaults={'structure_type': 'DUPLEX', 'year_built': 2008, 'condition_score': 5})

                                                             
        users_spec = [
            ('admin_user', 'admin@rchms.local', Role.ADMIN, None, True),
            ('helen_officer', 'helen@rchms.local', Role.HOUSING_OFFICER, c1, False),
            ('sam_supervisor', 'sam@rchms.local', Role.MAINTENANCE_SUPERVISOR, None, False),
            ('mia_manager', 'mia@rchms.local', Role.COMMUNITY_MANAGER, c1, False),
            ('tom_tenant', 'tom@rchms.local', Role.TENANT, None, False),
            ('alice_tenant', 'alice@rchms.local', Role.TENANT, None, False),
        ]
        for username, email, role, community, is_super in users_spec:
            u, created = User.objects.get_or_create(
                username=username, defaults={'email': email})
            if created:
                u.set_password('Passw0rd!')
                if is_super:
                    u.is_superuser = True
                    u.is_staff = True
                u.save()
            u.profile.role = role
            u.profile.community = community
            u.profile.save()

        tom = User.objects.get(username='tom_tenant')
        alice = User.objects.get(username='alice_tenant')

                            
        RepairRequest.objects.get_or_create(
            dwelling=d1, raised_by=tom,
            title='Leaking kitchen tap',
            defaults={
                'description': 'Drips constantly even when closed.',
                'category': 'PLUMBING', 'priority': 'MEDIUM',
            })
        RepairRequest.objects.get_or_create(
            dwelling=d2, raised_by=alice,
            title='Broken front window',
            defaults={
                'description': 'Cracked, lets in rain.',
                'category': 'STRUCTURAL', 'priority': 'HIGH',
            })

        self.stdout.write(self.style.SUCCESS('Done.'))
        self.stdout.write('All users have password: Passw0rd!')
        self.stdout.write('Superuser: admin_user / Passw0rd!')
