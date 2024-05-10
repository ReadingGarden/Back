import logging
from ninja import Router
from auths.permissions import UserAuth
from book.bookService import book_service

from cores.schema import DataResp, HttpResp
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["book"])


@router.get(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="책 검색"
)
def get_book(request, query: str, start: int, maxResults: int):
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
