import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from push.views import send_book_push
from push.pushService import push_service

logger = logging.getLogger("django.server")


# APScheduler를 시작하는 함수
def start_scheduler():
    scheduler = BackgroundScheduler()

    # 매 분 정각(초가 0일 때) send_book_push 함수를 실행
    scheduler.add_job(push_service.send_book_push, CronTrigger(second="0"))

    # 에러 또는 성공 처리 이벤트
    def job_listener(event):
        if event.exception:
            logger.error(f"Job failed: {event.job_id}")
        else:
            logger.info(f"Job succeeded: {event.job_id}")

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # 스케줄러 시작
    scheduler.start()