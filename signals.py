                                                                   
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification, RepairRequest

logger = logging.getLogger('housing')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info('LOGIN: user=%s', user.username)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is not None:
        logger.info('LOGOUT: user=%s', user.username)


@receiver(post_save, sender=RepairRequest)
def notify_on_repair_request(sender, instance, created, **kwargs):
                                                             
    from .tasks import email_urgent_repair_to_housing_officer

    if created:
        logger.info('REPAIR CREATED: id=%s title=%s priority=%s',
                    instance.pk, instance.title, instance.priority)
        if instance.raised_by:
            Notification.objects.create(
                recipient=instance.raised_by,
                repair_request=instance,
                message=f'Your repair request "{instance.title}" has been logged.',
            )
                                                           
        if instance.priority == RepairRequest.Priority.URGENT:
            email_urgent_repair_to_housing_officer.delay(instance.pk)
    else:
        logger.info('REPAIR UPDATED: id=%s status=%s', instance.pk, instance.status)
