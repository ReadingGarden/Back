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
    scheduler = BackgroundScheduler(job_defaults={
    'max_instances': 3,  # 모든 작업의 최대 실행 인스턴스 수
    'coalesce': True     # 이전 작업이 끝나지 않았으면 건너뛰지 않고 대기
})

    # 매 분 정각(초가 0일 때) send_book_push 함수를 실행
    scheduler.add_job(push_service.send_book_push, CronTrigger(second="0"))

    # 에러 또는 성공 처리 이벤트
    def job_listener(event):
        if event.exception:
            logger.error(f"Job failed: {event.job_id}")
        else:
            logger.info(f"Job succeeded: {event.job_id}")

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    if not scheduler.running:  # 스케줄러가 실행 중인지 확인
        scheduler.start()