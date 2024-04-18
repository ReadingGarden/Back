
import json
import logging
import requests
from book import settings
from cores.schema import DataResp

from cores.utils import session_wrapper


logger = logging.getLogger("django.server")

class BookService:
    @session_wrapper
    def get_book(self, session, request, query: str, start: int, maxResults: int):
        """
        책 검색
        """
        try:
            KEY = settings.ALADIN_TTBKEY
            # URL = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={KEY}&itemIdType=ISBN&ItemId=K762839932&output=js&Version=20131101&OptResult=ebookList,usedList,reviewList"
            URL = f"http://www.aladin.co.kr/ttb/api/ItemSearch.aspx?ttbkey={KEY}&Query={query}&QueryType=Keyword&MaxResults={maxResults}&start={start}&SearchTarget=BOOK&output=js&Version=20131101"

            book_response = requests.get(URL)
            # JSON 형식의 텍스트 데이터를 파이썬 딕셔너리로 변환합니다.
            response_json = json.loads(book_response.text)

            return DataResp(
                    resp_code=200, resp_msg="책 검색 성공", data=response_json)
        except Exception as e:
            logger.error(e)
            raise e
        
    @session_wrapper
    def get_book_detail(self, session, request, itemId: str):
        """
        책 상세 조회
        """
        try:
            KEY = settings.ALADIN_TTBKEY
            URL = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={KEY}&itemIdType=ISBN13&ItemId={itemId}&output=js&Version=20131101"
            
            book_response = requests.get(URL)
            # JSON 형식의 텍스트 데이터를 파이썬 딕셔너리로 변환합니다.
            response_json = json.loads(book_response.text)

            return DataResp(
                    resp_code=200, resp_msg="책 상세 조회 성공", data=response_json)
        except Exception as e:
            logger.error(e)
            raise e
        

book_service = BookService()