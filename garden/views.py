import logging
from django.shortcuts import render
from ninja import Router, Schema
from pydantic import BaseModel, Field
from auths.permissions import UserAuth

from cores.schema import HttpResp
from cores.utils import RETURN_FUNC
from garden.gardenService import garden_service

logger = logging.getLogger("django.server")
router = Router(tags=["garden"])

class CreateGardenSchema(Schema, BaseModel):
    garden_title: str = Field("", alias="garden_title")
    garden_info: str = Field("", alias="garden_info")
    garden_color: str = Field("red", alias="garden_color")

    
@router.post(
    "/",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 500: HttpResp},
    summary="가든 생성"
)
def create_garden(request, form: CreateGardenSchema):
    """
    가든 생성
    """
    return RETURN_FUNC(garden_service.create_garden(request, form.dict()))