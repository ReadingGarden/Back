
from datetime import datetime
import json
import logging
import jwt
import requests
from auths.models import User
from auths.tokenService import token_service
from book import settings
from book.models import Book, Book_Read
from cores.schema import DataResp, HttpResp

from cores.utils import GenericPayload, session_wrapper
from garden.models import Garden, GardenUser


logger = logging.getLogger("django.server")

class BookService:
    @session_wrapper
    def get_book(self, session, request, query: str, start: int, maxResults: int):
        """
        책 검색
        """
        try:
            KEY = settings.ALADIN_TTBKEY
            URL = f"http://www.aladin.co.kr/ttb/api/ItemSearch.aspx?ttbkey={KEY}&Query={query}&QueryType=Keyword&MaxResults={maxResults}&start={start}&SearchTarget=BOOK&output=js&Version=20131101"

            book_response = requests.get(URL)
            # JSON 형식의 텍스트 데이터를 파이썬 딕셔너리로 변환합니다.
            response_json = json.loads(book_response.text)

            return DataResp(
                    resp_code=200, resp_msg="책 검색 성공", data=response_json)
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')    
        except Exception as e:
            logger.error(e)
            raise e
        

    @session_wrapper
    def get_isbn_book(self, session, request, query: str):
        """
        책 검색
        """
        try:
            KEY = settings.ALADIN_TTBKEY
            URL = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={KEY}&itemIdType=ISBN&ItemId={query}&output=js&Version=20131101&"

            book_response = requests.get(URL)
            # JSON 형식의 텍스트 데이터를 파이썬 딕셔너리로 변환합니다.
            response_json = json.loads(book_response.text)

            return DataResp(
                    resp_code=200, resp_msg="책 검색(ISBN) 성공", data=response_json)
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')    
        except Exception as e:
            logger.error(e)
            raise e
        

    @session_wrapper
    def get_book_detail(self, session, request, query: str):
        """
        책 상세 조회
        """
        try:
            KEY = settings.ALADIN_TTBKEY
            URL = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={KEY}&itemIdType=ISBN13&ItemId={query}&output=js&Version=20131101"
            
            book_response = requests.get(URL)
            # JSON 형식의 텍스트 데이터를 파이썬 딕셔너리로 변환합니다.
            response_json = json.loads(book_response.text)

            result = {
                'searchCategoryId': response_json['searchCategoryId'],
                'searchCategoryName': response_json['searchCategoryName'],
                'title': response_json['item'][0]['title'],
                # 'link': response_json['item'][0]['link'],
                'author': response_json['item'][0]['author'],
                # 'pubdate': response_json['item'][0]['pubdate'],
                # 'description': response_json['item'][0]['description'],
                'isbn13': response_json['item'][0]['isbn13'],
                'cover': response_json['item'][0]['cover'],
                'publisher': response_json['item'][0]['publisher'],
                'itemPage': response_json['item'][0]['subInfo']['itemPage'],
            }
            
            #TODO - 
            result['record'] = {}
            result['memo'] = {}

            return DataResp(
                    resp_code=200, resp_msg="책 상세 조회 성공", data=result)
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')    
        except Exception as e:
            logger.error(e)
            raise e


    @session_wrapper
    def create_book(self, session, request, payload: GenericPayload):
        """
        책 등록
        """
        try:
            token = request.headers.get("Authorization")
            if token is not None:
                token = token.split(" ")[1]
            else:
                return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = token_service.verify_access_token(token)
            if not(
                user_instance := session.query(User)
                .filter(User.user_no == token_payload['user_no'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 사용자 정보가 없습니다.")
            
            # 가든 존재
            if not (
                session.query(Garden)
                .filter(Garden.garden_no == payload['garden_no'], user_instance.user_no == GardenUser.user_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든이 없습니다.")
                
            
            #TODO - 나무 타입 선택
            new_book = Book(
                **payload,
                user_no=user_instance.user_no
            )

            session.add(new_book)
            session.commit()
            session.refresh(new_book)

            return HttpResp(resp_code=201, resp_msg="책 등록 성공")
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e
        

    @session_wrapper
    def delete_book(self, session, request, book_no: str):
        try:
            token = request.headers.get("Authorization")
            if token is not None:
                token = token.split(" ")[1]
            else:
                return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = token_service.verify_access_token(token)
            if not(
                user_instance := session.query(User)
                .filter(User.user_no == token_payload['user_no'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 사용자 정보가 없습니다.")
            
            if not (
                book_instance := session.query(Book).filter(Book.book_no ==  book_no, Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            session.delete(book_instance)
            session.commit()

            return HttpResp(resp_code=200, resp_msg="책 삭제 성공")
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e
        

    @session_wrapper
    def update_book(self, session, request, payload:GenericPayload,  book_no:str):
        try:
            token = request.headers.get("Authorization")
            if token is not None:
                token = token.split(" ")[1]
            else:
                return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = token_service.verify_access_token(token)
            if not(
                user_instance := session.query(User)
                .filter(User.user_no == token_payload['user_no'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 사용자 정보가 없습니다.")
            
            if not (
                book_instance := session.query(Book).filter(Book.book_no ==  book_no, Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            book_instance.garden_no = payload['garden_no']
            book_instance.book_title = payload['book_title']
            book_instance.book_author = payload['book_author']
            book_instance.book_publisher = payload['book_publisher']
            book_instance.book_status = payload['book_status']

            session.add(book_instance)
            session.commit()
            session.refresh(book_instance)

            return HttpResp(resp_code=200, resp_msg="책 수정 성공")
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e
        
    
    @session_wrapper
    def get_book_status(self, session, request, garden_no:int=None, status:int=0):
        try:
            token = request.headers.get("Authorization")
            if token is not None:
                token = token.split(" ")[1]
            else:
                return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = token_service.verify_access_token(token)
            if not(
                user_instance := session.query(User)
                .filter(User.user_no == token_payload['user_no'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 사용자 정보가 없습니다.")
            
            book_query = (
                session.query(Book)
                    .filter(Book.user_no == user_instance.user_no, Book.book_status == status)
            )
            
            if garden_no is not None:
                book_query = book_query.filter(Book.garden_no == garden_no)

            book_instance = book_query.all()

            #TODO - 나머지도
            result = [
                {
                    'book_no': book.book_no,
                    'book_title': book.book_title,
                    'book_author': book.book_author,
                    'book_publisher': book.book_publisher,
                    'book_status': book.book_status,
                    'book_page': book.book_page,
                    'garden_no': book.garden_no,
                }
                for book in book_instance
            ]
            
            return DataResp(resp_code=200, resp_msg="책 상태 조회 성공", data=result)
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e
        

    @session_wrapper
    def create_read(self, session, request, payload: GenericPayload):
        try:
            token = request.headers.get("Authorization")
            if token is not None:
                token = token.split(" ")[1]
            else:
                return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = token_service.verify_access_token(token)
            if not(
                user_instance := session.query(User)
                .filter(User.user_no == token_payload['user_no'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 사용자 정보가 없습니다.")
            
            if not (
                book_instance := session.query(Book).filter(Book.book_no == payload['book_no'], Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            new_Read = Book_Read(
                **payload,
                user_no = user_instance.user_no
            )

            if not (
                session.query(Book_Read)
                .filter(Book_Read.book_no == payload['book_no'], Book_Read.user_no == user_instance.user_no)
                .first()
            ):
                new_Read.book_start_date = datetime.now()

            session.add(new_Read)
            session.commit()
            session.refresh(new_Read)

            percent = new_Read.book_current_page/book_instance.book_page
            
            return DataResp(resp_code=201, resp_msg="책 기록 성공", data={
                'book_current_page': payload['book_current_page'],
                'percent': percent
            })
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e


        

book_service = BookService()