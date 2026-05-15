                                                    
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

                                                                      
app.conf.beat_schedule = {
    'weekly-maintenance-summary': {
        'task': 'housing.tasks.send_weekly_maintenance_summary',
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
