from datetime import datetime
import logging
from django.shortcuts import render
from ninja import Router, Schema
from pydantic import BaseModel, Field

from push.pushService import push_service
from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["push"])

class UpdatePushShema(Schema, BaseModel):
    push_app_ok: bool = Field(None, alias="push_app_ok")
    push_book_ok: bool = Field(None, alias="push_book_ok")
    push_time: datetime = Field(None, alias="push_time")

# @router.post("/",
#              response={201: HttpResp, 409: HttpResp, 500: HttpResp}, 
#              summary="푸시 알림 등록")
# def create_push(request, form: {}):
#     """
#     푸시 알림 등록
#     """
#     logger.info(f"Call create_push API")
#     return RETURN_FUNC(push_service.create_push(request))


@router.put("/",
             response={200: HttpResp, 400: HttpResp, 500: HttpResp}, 
             summary="푸시 알림 수정")
def update_push(request, form: UpdatePushShema):
    """
    푸시 알림 수정
    """
    logger.info(f"Call create_push API")
    return RETURN_FUNC(push_service.update_push(request, form.dict()))
    
