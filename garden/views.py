import logging
from django.shortcuts import render
from ninja import Router, Schema
from pydantic import BaseModel, Field
from auths.permissions import UserAuth

from cores.schema import DataResp, HttpResp
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
    response={201: DataResp, 400: HttpResp, 401: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="가든 추가"
)
def create_garden(request, form: CreateGardenSchema):
    return RETURN_FUNC(garden_service.create_garden(request, form.dict()))


@router.get(
    "/list",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="가든 리스트 조회"
)
def get_garden(request):
    return RETURN_FUNC(garden_service.get_garden(request))


@router.get(
    "/detail",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="가든 상세 조회"
)
def get_garden_detail(request, garden_no: int):
    return RETURN_FUNC(garden_service.get_garden_detail(request, garden_no))


@router.put(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="가든 수정"
)
def update_garden(request, form: CreateGardenSchema, garden_no: int):
    return RETURN_FUNC(garden_service.update_garden(request, form.dict(), garden_no))


@router.delete(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="가든 삭제"
)
def delete_garden(request, garden_no: int):
    return RETURN_FUNC(garden_service.delete_garden(request, garden_no))


