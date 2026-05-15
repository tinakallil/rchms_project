   
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import (
    Community, Dwelling, RepairRequest, MaintenanceUpdate,
    Notification, Role,
)
                                                                            
def _create_user(username, role, community=None, email=None, password='Passw0rd!'):
                                                              
    user = User.objects.create_user(username=username, password=password,
                                    email=email or f'{username}@example.com')
    profile = user.profile                          
    profile.role = role
    profile.community = community
    profile.save()
    return user

                                                                             
class ModelTests(TestCase):
    def setUp(self):
        self.community = Community.objects.create(name='Yuendumu', region='NT')
        self.dwelling = Dwelling.objects.create(
            community=self.community,
            address='12 Acacia St',
            structure_type=Dwelling.Structure.HOUSE,
            year_built=2010,
            condition_score=7,
        )
        self.tenant_user = _create_user('alice', Role.TENANT)

    def test_community_str(self):
        self.assertIn('Yuendumu', str(self.community))

    def test_dwelling_str(self):
        self.assertIn('Acacia', str(self.dwelling))
        self.assertIn('Yuendumu', str(self.dwelling))

    def test_repair_request_defaults(self):
        rr = RepairRequest.objects.create(
            dwelling=self.dwelling,
            raised_by=self.tenant_user,
            title='Leaking tap',
            description='Kitchen tap drips.',
        )
        self.assertEqual(rr.status, RepairRequest.Status.OPEN)
        self.assertEqual(rr.priority, RepairRequest.Priority.MEDIUM)
        self.assertFalse(rr.is_urgent)

    def test_repair_request_urgent_creates_notification(self):
                                                                  
        self.assertEqual(Notification.objects.count(), 0)
        rr = RepairRequest.objects.create(
            dwelling=self.dwelling,
            raised_by=self.tenant_user,
            title='Burst pipe',
            description='Flooding bathroom!',
            priority=RepairRequest.Priority.HIGH,
        )
        self.assertEqual(Notification.objects.filter(recipient=self.tenant_user).count(), 1)
        self.assertIn(rr.title, Notification.objects.first().message)

    def test_maintenance_update_attached(self):
        rr = RepairRequest.objects.create(
            dwelling=self.dwelling, raised_by=self.tenant_user,
            title='X', description='Y',
        )
        MaintenanceUpdate.objects.create(
            repair_request=rr, author=self.tenant_user, note='Started work',
        )
        self.assertEqual(rr.updates.count(), 1)


                                                                             
                   
                                                                             
class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.community = Community.objects.create(name='Maningrida', region='NT')
        self.dwelling = Dwelling.objects.create(
            community=self.community,
            address='5 Bauhinia Rd',
            structure_type=Dwelling.Structure.UNIT,
            year_built=2015,
        )
        self.tenant = _create_user('tom_tenant', Role.TENANT)
        self.officer = _create_user('helen_officer', Role.HOUSING_OFFICER,
                                    community=self.community)
        self.other_tenant = _create_user('eve_tenant', Role.TENANT)

    def test_login_required_redirects(self):
        url = reverse('repair_request_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_tenant_can_create_repair(self):
        self.client.login(username='tom_tenant', password='Passw0rd!')
        response = self.client.post(reverse('repair_request_create'), {
            'dwelling': self.dwelling.pk,
            'title': 'Broken window',
            'description': 'Front window cracked.',
            'category': RepairRequest.Category.STRUCTURAL,
            'priority': RepairRequest.Priority.MEDIUM,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RepairRequest.objects.count(), 1)
        self.assertEqual(RepairRequest.objects.first().raised_by, self.tenant)

    def test_tenant_only_sees_own_requests(self):
        rr_mine = RepairRequest.objects.create(
            dwelling=self.dwelling, raised_by=self.tenant,
            title='Mine', description='.',
        )
        rr_other = RepairRequest.objects.create(
            dwelling=self.dwelling, raised_by=self.other_tenant,
            title='Other', description='.',
        )
        self.client.login(username='tom_tenant', password='Passw0rd!')
        response = self.client.get(reverse('repair_request_list'))
        self.assertContains(response, rr_mine.title)
        self.assertNotContains(response, rr_other.title)

    def test_housing_officer_sees_all_in_community(self):
        RepairRequest.objects.create(
            dwelling=self.dwelling, raised_by=self.tenant,
            title='Officer-visible', description='.',
        )
        self.client.login(username='helen_officer', password='Passw0rd!')
        response = self.client.get(reverse('repair_request_list'))
        self.assertContains(response, 'Officer-visible')

    def test_tenant_cannot_view_other_tenants_detail(self):
        rr_other = RepairRequest.objects.create(
            dwelling=self.dwelling, raised_by=self.other_tenant,
            title='Private', description='.',
        )
        self.client.login(username='tom_tenant', password='Passw0rd!')
        response = self.client.get(
            reverse('repair_request_detail', args=[rr_other.pk]))
        self.assertEqual(response.status_code, 403)

    def test_tenant_can_delete_own_open_request(self):
        rr = RepairRequest.objects.create(
            dwelling=self.dwelling, raised_by=self.tenant,
            title='Cancel me', description='.',
        )
        self.client.login(username='tom_tenant', password='Passw0rd!')
        response = self.client.post(
            reverse('repair_request_delete', args=[rr.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RepairRequest.objects.count(), 0)


class CeleryTaskTests(TestCase):
                                                                       
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.test import override_settings
        cls._override = override_settings(
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_TASK_EAGER_PROPAGATES=True,
        )
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        super().tearDownClass()

    def test_weekly_summary_returns_count(self):
        from .tasks import send_weekly_maintenance_summary

        community = Community.objects.create(name='Wadeye', region='NT')
        supervisor = _create_user(
            'sam_sup', Role.MAINTENANCE_SUPERVISOR,
            email='sam@example.com',
        )
                                                             
        result = send_weekly_maintenance_summary()
        self.assertIn('Sent to', result)
