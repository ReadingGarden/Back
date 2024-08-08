from datetime import datetime
import logging
from ninja import File, Router, Schema
from ninja.files import UploadedFile
from pydantic import BaseModel, Field
from auths.permissions import UserAuth
from book.bookService import book_service

from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["book"])

class CreateBookShema(Schema, BaseModel):
    book_isbn: str = Field(None, alias="book_isbn")
    garden_no: int = Field(None, alias="garden_no")
    book_title: str = Field(..., alias="book_title")
    book_author: str = Field(..., alias="book_author")
    book_publisher: str = Field(..., alias="book_publisher")
    book_tree: str = Field(None, alias="book_tree")
    book_image_url: str = Field(None, alias="book_image_url")
    book_status: int = Field(..., alias="book_status")
    book_page: int = Field(...,alias="book_page")

class UpdateBookShema(Schema, BaseModel):
    garden_no: int = Field(None, alias="garden_no", )
    # book_title: str = Field(..., alias="book_title")
    # book_author: str = Field(..., alias="book_author")
    # book_publisher: str = Field(..., alias="book_publisher")
    book_tree: str = Field(None, alias="book_tree")
    # book_image_url: str = Field(None, alias="book_image_url")
    book_status: int = Field(None, alias="book_status")

class CreateReadShema(Schema, BaseModel):
    book_no: int = Field(..., alias="book_no")
    book_start_date: datetime = Field(None, alias="book_start_date")
    book_end_date: datetime = Field(None, alias="book_end_date")
    book_current_page: int = Field(..., alias="book_current_page")


@router.get(
    "/search",
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
    "/search-isbn",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 검색(ISBN)"
)
def get_isbn_book(request, query: str,):
    """
    * query: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call get_isbn_book API")
    return RETURN_FUNC(book_service.get_isbn_book(request, query))


@router.get(
    "/detail-isbn",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 상세 조회"
)
def get_book_detail(request, query: str):
    """
    * query: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call get_book_detail API")
    return RETURN_FUNC(book_service.get_book_detail(request, query))


@router.post(
    "/",
    auth=UserAuth(),
    response={201: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 등록"
)
def create_book(request, form:CreateBookShema):
    """
    * book_isbn: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call post_book API")
    return RETURN_FUNC(book_service.create_book(request, form.dict()))


@router.delete(
    "/",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 삭제"
)
def delete_book(request, book_no:int):
    logger.info(f"Call delete_book API")
    return RETURN_FUNC(book_service.delete_book(request, book_no))


@router.put(
    "/",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="책 수정"
)
def update_book(request, form:UpdateBookShema, book_no: int):
    logger.info(f"Call update_book API")
    return RETURN_FUNC(book_service.update_book(request, form.dict(),  book_no))


@router.get(
    "/status",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 상태(목록) 리스트 조회"
)
def get_book_status(request, garden_no:int=None, status:int=None):
    """
    * book_image_url: 알라딘 표지
    * book_image_url2: 자체 표지
    * status: 0읽는중, 1읽은책, 2읽고싶은책, 3읽는중or읽은책
    """
    logger.info(f"Call get_book_status API")
    return RETURN_FUNC(book_service.get_book_status(request,garden_no, status))

@router.get(
    "/read",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="독서 기록 조회"
)
def get_read(request, book_no:int):
    """
    * book_image_url: 알라딘 표지
    * book_image_url2: 자체 표지
    """
    logger.info(f"Call get_read API")
    return RETURN_FUNC(book_service.get_read(request, book_no))

@router.post(
    "/read",
    auth=UserAuth(),
    response={201: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="독서 기록 추가"
)
def create_read(request, form:CreateReadShema):
    logger.info(f"Call create_read API")
    return RETURN_FUNC(book_service.create_read(request, form.dict()))

@router.delete(
    "/read",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="독서 기록 삭제"
)
def delete_read(request, id: int):
    logger.info(f"Call delete_read API")
    return RETURN_FUNC(book_service.delete_read(request, id))

@router.post(
    "/image",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 이미지 업로드",
)
def upload_book_image(request, book_no:int, file: UploadedFile = File(...)):
    logger.info(f"Call upload_book_image API")
    return RETURN_FUNC(book_service.upload_book_image(request, book_no, file))

@router.delete(
    "/image",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 이미지 삭제",
)
def delete_book_image(request, book_no:int):
    logger.info(f"Call delete_book_image API")
    return RETURN_FUNC(book_service.delete_book_image(request, book_no))

# @router.post(
#     "/image",
#     auth=UserAuth(),
#     response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
#     summary="책 이미지 업로드",
# )
# def upload_book_image(request, book_no:int, file: UploadedFile = File(...)):
#     logger.info(f"Call upload_book_image API")
#     return RETURN_FUNC(book_service.upload_book_image(request, book_no, file))






