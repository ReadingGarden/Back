import logging
from ninja import Router, Schema
from pydantic import BaseModel, Field
from auths.permissions import UserAuth
from book.bookService import book_service

from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["book"])

class CreateBookShecma(Schema, BaseModel):
    book_no: str = Field(..., alias="book_no")
    garden_no: int = Field(..., alias="garden_no")
    book_title: str = Field(..., alias="book_title")
    book_author: str = Field(..., alias="book_author")
    book_publisher: str = Field(..., alias="book_publisher")
    book_status: int = Field(..., alias="book_status")

class PutBookShecma(Schema, BaseModel):
    garden_no: int = Field(..., alias="garden_no", )
    book_title: str = Field(..., alias="book_title")
    book_author: str = Field(..., alias="book_author")
    book_publisher: str = Field(..., alias="book_publisher")
    book_status: int = Field(..., alias="book_status")


@router.get(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 검색"
)
def get_book(request, query: str, start: int=1, maxResults: int=100):
    """
    * start: 검색결과 시작페이지
    * maxResults: 검색결과 한 페이지당 최대 출력 개수
    """
    logger.info(f"Call get_book API")
    return RETURN_FUNC(book_service.get_book(request, query, start, maxResults))


@router.get(
    "/detail",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 상세 조회"
)
def get_book_detail(request, itemId: str):
    """
    * itemId: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call get_book_detail API")
    return RETURN_FUNC(book_service.get_book_detail(request, itemId))


@router.post(
    "/",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 등록"
)
def create_book(request, form:CreateBookShecma):
    """
    * book_no: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call post_book API")
    return RETURN_FUNC(book_service.create_book(request, form.dict()))


@router.delete(
    "/",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 삭제"
)
def delete_book(request, book_no:str):
    """
    * book_no: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call delete_book API")
    return RETURN_FUNC(book_service.delete_book(request, book_no))


@router.put(
    "/",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 수정"
)
def update_book(request, form:PutBookShecma, book_no: str):
    """
    * book_no: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call put_book API")
    return RETURN_FUNC(book_service.update_book(request, form.dict(),  book_no))


