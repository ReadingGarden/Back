from datetime import datetime
import logging
from django.shortcuts import render
from ninja import Router, Schema
from pydantic import BaseModel, Field

from auths.permissions import UserAuth
from push.pushService import push_service
from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["push"])

class UpdatePushShema(Schema, BaseModel):
    push_app_ok: bool = Field(None, alias="push_app_ok")
    push_book_ok: bool = Field(None, alias="push_book_ok")
    push_time: datetime = Field(None, alias="push_time")

@router.get("/",
            auth=UserAuth(),
             response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp}, 
             summary="푸시 알림 조회")
def get_push(request):
    """
    푸시 알림 조회
    """
    logger.info(f"Call get_push API")
    return RETURN_FUNC(push_service.get_push(request))

@router.put("/",
            auth=UserAuth(),
            response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp}, 
            summary="푸시 알림 수정")
def update_push(request, form: UpdatePushShema):
    """
    푸시 알림 수정
    """
    logger.info(f"Call create_push API")
    return RETURN_FUNC(push_service.update_push(request, form.dict()))

@router.post("/book",
            response={200: DataResp, 400: HttpResp, 500: HttpResp}, 
            summary="푸시 알림 전송 (독서 알림)")
def send_book_push(request):
    """
    FCM 멀티캐스트 푸시 알림 보내기 (독서 알림)
    """
    logger.info(f"Call send_push_notification API")
    return RETURN_FUNC(push_service.send_book_push())
    
