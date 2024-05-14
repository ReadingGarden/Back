import logging
from ninja import Router, Schema
from pydantic import BaseModel, Field
from auths.permissions import UserAuth
from book.bookService import book_service

from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["book"])

class CreateBookShema(Schema, BaseModel):
    book_no: str = Field(..., alias="book_no")
    garden_no: int = Field(..., alias="garden_no")
    book_title: str = Field(..., alias="book_title")
    book_author: str = Field(..., alias="book_author")
    book_publisher: str = Field(..., alias="book_publisher")
    book_status: int = Field(..., alias="book_status")
    book_page: int = Field(...,alias="book_page")

class UpdateBookShema(Schema, BaseModel):
    garden_no: int = Field(..., alias="garden_no", )
    book_title: str = Field(..., alias="book_title")
    book_author: str = Field(..., alias="book_author")
    book_publisher: str = Field(..., alias="book_publisher")
    book_status: int = Field(..., alias="book_status")
    #TODO: - 총 페이지 수정도 포함?

class CreateReadShema(Schema, BaseModel):
    book_no: str = Field(..., alias="book_no")
    book_current_page: int = Field(..., alias="book_current_page")

class MemoShema(Schema, BaseModel):
    book_no: str = Field(..., alias="book_no")
    memo_content: str = Field(..., alias="memo_content")
    memo_quote: str = Field(..., alias="memo_quote")


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
    "/isbn",
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
    "/detail",
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
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 등록"
)
def create_book(request, form:CreateBookShema):
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
def update_book(request, form:UpdateBookShema, book_no: str):
    """
    * book_no: ISBN13 입력 (9788937462788)
    """
    logger.info(f"Call update_book API")
    return RETURN_FUNC(book_service.update_book(request, form.dict(),  book_no))


@router.get(
    "/status",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 상태(목록) 리스트 조회"
)
def get_book_status(request, garden_no:int=None, status:int=0):
    """
    * status: 0읽는중, 1읽은책, 2읽고싶은책
    """
    logger.info(f"Call get_book_status API")
    return RETURN_FUNC(book_service.get_book_status(request,garden_no, status))

@router.get(
    "/read",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="독서 기록 조회"
)
def get_read(request, book_no:str):
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
    "/memo",
    auth=UserAuth(),
    response={201: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 추가"
)
def create_memo(request, form:MemoShema):
    logger.info(f"Call create_memo API")
    return RETURN_FUNC(book_service.create_memo(request, form.dict()))

@router.put(
    "/memo",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 수정"
)
def update_memo(request, form:MemoShema, id:int):
    logger.info(f"Call update_memo API")
    return RETURN_FUNC(book_service.update_memo(request, form.dict(), id))

@router.delete(
    "/memo",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 삭제"
)
def delete_memo(request, id:int):
    logger.info(f"Call delete_memo API")
    return RETURN_FUNC(book_service.delete_memo(request, id))

@router.get(
    "/memo",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 리스트 조회"
)
def get_memo(request):
    logger.info(f"Call get_memo API")
    return RETURN_FUNC(book_service.get_memo(request))

@router.get(
    "/memo/detail",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 상세 조회"
)
def get_memo_detail(request, id:int):
    logger.info(f"Call get_memo_detail API")
    return RETURN_FUNC(book_service.get_memo_detail(request, id))

@router.put(
    "/memo/like",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="메모 즐겨찾기 추가/해제"
)
def like_memo(request, id:int):
    logger.info(f"Call like_memo API")
    return RETURN_FUNC(book_service.like_memo(request, id))






