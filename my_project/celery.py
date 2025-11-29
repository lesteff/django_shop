import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')

app = Celery('my_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-exchange-rates-daily': {
        'task': 'myapp.tasks.fetch_exchange_rates',
        'schedule': crontab(hour=10, minute=0),  # Каждый день в 10:00
    },
    'fetch-exchange-rates-backup': {
        'task': 'myapp.tasks.fetch_exchange_rates',
        'schedule': crontab(hour=16, minute=0),  # Резервное обновление в 16:00
    },
    'send-daily-report': {
        'task': 'myapp.tasks.send_daily_products_report',
        'schedule': crontab(hour=9, minute=0),  # Каждый день в 9:00
    },
}
