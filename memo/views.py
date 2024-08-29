import logging
from ninja import File, Router, Schema
from ninja.files import UploadedFile
from pydantic import BaseModel, Field
from auths.permissions import UserAuth
from memo.memoService import memo_service

from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["memo"])

class MemoShema(Schema, BaseModel):
    book_no: int = Field(..., alias="book_no")
    memo_content: str = Field(..., alias="memo_content")
    # memo_quote: str = Field(..., alias="memo_quote")


@router.post(
    "/",
    auth=UserAuth(),
    response={201: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 추가"
)
def create_memo(request, form:MemoShema):
    logger.info(f"Call create_memo API")
    return RETURN_FUNC(memo_service.create_memo(request, form.dict()))

@router.put(
    "/",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 수정"
)
def update_memo(request, form:MemoShema, id:int):
    logger.info(f"Call update_memo API")
    return RETURN_FUNC(memo_service.update_memo(request, form.dict(), id))
 
@router.delete(
    "/",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 삭제"
)
def delete_memo(request, id:int):
    logger.info(f"Call delete_memo API")
    return RETURN_FUNC(memo_service.delete_memo(request, id))

@router.get(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 리스트 조회"
)
def get_memo(request, page: int = 1, page_size: int = 10):
    logger.info(f"Call get_memo API")
    return RETURN_FUNC(memo_service.get_memo(request, page, page_size))

@router.get(
    "/detail",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 상세 조회"
)
def get_memo_detail(request, id:int):
    logger.info(f"Call get_memo_detail API")
    return RETURN_FUNC(memo_service.get_memo_detail(request, id))

@router.put(
    "/like",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 즐겨찾기 추가/해제"
)
def like_memo(request, id:int):
    logger.info(f"Call like_memo API")
    return RETURN_FUNC(memo_service.like_memo(request, id))

@router.post(
    "/image",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 이미지 업로드",
)
def upload_memo_image(request, id:int, file: UploadedFile = File(...)):
    logger.info(f"Call upload_memo_image API")
    return RETURN_FUNC(memo_service.upload_memo_image(request, id, file))

@router.delete(
    "/image",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 이미지 삭제",
)
def delete_memo_image(request, id:int):
    logger.info(f"Call delete_memo_image API")
    return RETURN_FUNC(memo_service.delete_memo_image(request, id))