from apscheduler.schedulers.background import BackgroundScheduler
from .views import BackgroundClass


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(BackgroundClass.test_func, 'interval', minutes=1)
    scheduler.add_job(BackgroundClass.power_allot_func, 'interval', minutes=1)
    scheduler.add_job(BackgroundClass.device_consumption, 'interval', minutes=1)
    scheduler.start()
