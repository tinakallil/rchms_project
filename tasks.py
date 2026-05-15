                                        
import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger('housing')


@shared_task
def email_urgent_repair_to_housing_officer(repair_request_id):
    
    from .models import RepairRequest, UserProfile, Role, Notification

    try:
        rr = RepairRequest.objects.select_related('dwelling__community').get(pk=repair_request_id)
    except RepairRequest.DoesNotExist:
        logger.error('Urgent repair email: repair %s not found', repair_request_id)
        return

    officers = UserProfile.objects.filter(
        role=Role.HOUSING_OFFICER,
        community=rr.dwelling.community,
    ).select_related('user')

    recipients = [p.user.email for p in officers if p.user.email]
    if not recipients:
        logger.warning('No housing officers with email for community %s', rr.dwelling.community)
        return

    subject = f'[URGENT] Repair request #{rr.pk} at {rr.dwelling.address}'
    body = (
        f'An urgent repair request was raised.\n\n'
        f'Title: {rr.title}\n'
        f'Description: {rr.description}\n'
        f'Dwelling: {rr.dwelling.address}\n'
        f'Community: {rr.dwelling.community.name}\n'
        f'Raised by: {rr.raised_by.username if rr.raised_by else "unknown"}\n'
        f'Created at: {rr.created_at:%Y-%m-%d %H:%M}\n'
    )
    send_mail(subject, body, None, recipients)

    for officer in officers:
        Notification.objects.create(
            recipient=officer.user,
            repair_request=rr,
            message=f'URGENT: new repair "{rr.title}" at {rr.dwelling.address}',
        )

    logger.info('Urgent repair email sent: repair=%s recipients=%s', rr.pk, recipients)
    return f'Sent to {len(recipients)} officer(s).'


@shared_task
def send_weekly_maintenance_summary():
       
    from .models import RepairRequest, UserProfile, Role

    since = timezone.now() - timedelta(days=7)
    open_requests = RepairRequest.objects.filter(
        status__in=[RepairRequest.Status.OPEN,
                    RepairRequest.Status.ASSIGNED,
                    RepairRequest.Status.IN_PROGRESS],
        created_at__gte=since,
    ).select_related('dwelling__community')

    supervisors = UserProfile.objects.filter(
        role=Role.MAINTENANCE_SUPERVISOR,
    ).select_related('user')

    lines = [
        f'#{r.pk} | {r.priority} | {r.dwelling.community.name} | '
        f'{r.dwelling.address} | {r.title} | {r.status}'
        for r in open_requests
    ]
    body = 'Weekly maintenance summary\n\n' + (
        '\n'.join(lines) if lines else 'No open requests in the last 7 days.'
    )

    sent = 0
    for sup in supervisors:
        if sup.user.email:
            send_mail(
                'RCHMS – Weekly Maintenance Summary',
                body,
                None,
                [sup.user.email],
            )
            sent += 1

    logger.info('Weekly summary sent to %s supervisor(s); %s open request(s).',
                sent, len(lines))
    return f'Sent to {sent} supervisor(s).'
