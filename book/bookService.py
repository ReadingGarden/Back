
import json
import logging
import os
import secrets
import jwt
import requests

from sqlalchemy import desc, or_

from datetime import datetime
from auths.models import User
from auths.tokenService import token_service
from book import settings
from book.models import Book, BookImage, BookRead
from cores.schema import DataResp, HttpResp

from cores.utils import GenericPayload, pagination, session_wrapper
from garden.models import Garden, GardenUser
from memo.models import Memo, MemoImage


logger = logging.getLogger("django.server")

class BookService:
    @session_wrapper
    def get_book(self, session, request, query: str, start: int, maxResults: int):
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
                'description': response_json['item'][0]['description'],
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
            ) and (payload['garden_no'] is not None):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든이 없습니다.")
                
            
            #TODO - 나무 타입 선택
            new_book = Book(
                **payload,
                user_no=user_instance.user_no
            )

            session.add(new_book)
            session.commit()
            session.refresh(new_book)

            return DataResp(resp_code=201, resp_msg="책 등록 성공", data={'book_no':new_book.book_no})
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
    def delete_book(self, session, request, book_no: int):
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
                book_instance := session.query(Book).filter(Book.book_no == book_no, Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            # 책 이미지 삭제
            image_instance = session.query(BookImage).filter(BookImage.book_no == book_no).first()
            if image_instance:
                # 서버, DB 저장된 이미지 삭제
                try:
                    os.remove('images/'+image_instance.image_url)
                    session.delete(image_instance)
                except FileNotFoundError:
                    pass

            # 메모 삭제 및 메모 이미지도 같이
            memo_instance = session.query(Memo).filter(Memo.book_no == book_no).all()
            for memo in memo_instance:
                memo_image_instance = session.query(MemoImage).filter(MemoImage.memo_no == memo.id).first()
                if memo_image_instance:
                    try:
                        os.remove('images/'+memo_image_instance.image_url)
                        session.delete(memo_image_instance)
                    except FileNotFoundError:
                        pass
                session.delete(memo)

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
    def update_book(self, session, request, payload:GenericPayload,  book_no:int):
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
                book_instance := session.query(Book).filter(Book.book_no == book_no, Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            if payload['garden_no']:
                # 책 옮기기
                book_instance2 = session.query(Book).filter(Book.garden_no == payload['garden_no']).all() # 도착지 가든의 책 인스턴스
                # 도착지 가든 + 현재 책 합 30개 이하만 가능
                if len(book_instance2) == 30:
                    return HttpResp(resp_code=403, resp_msg="가든 옮기기 불가")

            # book_instance.book_title = payload['book_title']
            # book_instance.book_author = payload['book_author']
            # book_instance.book_publisher = payload['book_publisher']
            # book_instance.book_image_url = payload['book_image_url']
            for key, value in payload.items():
                if value is not None:
                    setattr(book_instance, key, value)

            # if payload['book_tree']:
            #     book_instance.book_tree = payload['book_tree']
            # if payload['book_status']:
            #     book_instance.book_status = payload['book_status']

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
    def get_book_status(self, session, request, garden_no:int=None, status:int=None, page:int=1, page_size:int=10):
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
            
            # 전체 조회
            book_query = session.query(Book).filter(Book.user_no == user_instance.user_no)

            # 가든 필터 조회
            if garden_no is not None:
                book_query = book_query.filter(Book.garden_no == garden_no)

            # status 필터 조회
            if status is not None:
                if status == 3:
                    book_query = (
                    book_query
                    .filter(
                        Book.user_no == user_instance.user_no,
                        or_(Book.book_status == 0, Book.book_status == 1))
                    )
                else:
                    book_query = (book_query
                    .filter(Book.user_no == user_instance.user_no, Book.book_status == status)
                    )

            # 페이지네이션 적용 (예: 1페이지, 페이지당 10개 항목)
            pagination_result = pagination(book_query, page=page, page_size=page_size)
            
            # 페이지네이션된 결과에서 책 리스트 추출
            book_status_list = []            
            for book in pagination_result['list']:
                percent = 0.0
                if (
                        book_read_instance := 
                        session.query(BookRead)
                        .filter(BookRead.book_no == book.book_no)
                        .order_by(desc(BookRead.created_at))
                        .first()
                    ):
                        percent = (book_read_instance.book_current_page/book.book_page)*100

                book_status_list.append({
                    'book_no': book.book_no,
                    'book_title': book.book_title,
                    'book_author': book.book_author,
                    'book_publisher': book.book_publisher,
                    'book_image_url': book.book_image_url,
                    # 'book_image_url2': (
                    #     (image_instance.image_url if image_instance else '')
                    #         if (image_instance := session.query(BookImage)
                    #             .filter(BookImage.book_no == book.book_no)
                    #             .first())
                    #         else None
                    # ),
                    'book_tree': book.book_tree,
                    'book_status': book.book_status,
                    'percent': percent,
                    'book_page': book.book_page,
                    'garden_no': book.garden_no,
                })

            # 최종 결과에 페이지네이션 정보 추가
            result = {
               "current_page": pagination_result["current_page"],
               "max_page": pagination_result["max_page"],
               "total_items": pagination_result["total"],
               "page_size": pagination_result["page_size"],
               "list": book_status_list
            }
            
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
    def get_read(self, session, request, book_no:int):
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
            
            # Book, Garden join
            if not (
                book_garden_instance := session.query(Book, Garden)
                .join(Garden, Book.garden_no == Garden.garden_no)
                .filter(Book.book_no == book_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            book, garden = book_garden_instance

            result = {
                'garden_no': garden.garden_no,
                'book_title': book.book_title,
                'book_author': book.book_author,
                'book_publisher': book.book_publisher,
                'book_image_url': book.book_image_url,
                # 'book_image_url2': (
                #     (image_instance.image_url if image_instance else '')
                #         if (image_instance := session.query(BookImage)
                #             .filter(BookImage.book_no == book.book_no)
                #             .first())
                #         else None
                # ),
                'book_tree': book.book_tree,
                'book_status': book.book_status,
                'book_page': book.book_page,
                'book_current_page': 0,
                'percent': 0.0,
                'user_no': book.user_no
            }
            
            # 쿼리에서 조건에 맞는 BookRead 인스턴스를 찾습니다.
            book_read_query = (
                session.query(BookRead)
                .filter(BookRead.book_no == book_no, BookRead.user_no == user_instance.user_no)
            )
            result['book_read_list'] = []

            # 결과가 있을 경우
            if book_read_query.first():
                # 가장 최근의 BookRead 인스턴스를 가져옵니다.
                book_read_instance = book_read_query.order_by(BookRead.created_at.desc()).first()

                result['percent'] = (book_read_instance.book_current_page/book.book_page)*100
                result['book_current_page'] = book_read_instance.book_current_page

                # 독서 기록 리스트                
                book_read_instances = book_read_query.order_by(BookRead.created_at.desc()).all()
                result['book_read_list'] = [
                    {
                        'id': book_read.id,
                        'book_current_page': book_read.book_current_page,
                        'book_start_date': book_read.book_start_date,
                        'book_end_date': book_read.book_end_date,
                    }
                    for book_read in book_read_instances
                ]

            # 메모 리스트
            memo_instance = session.query(Memo).filter(Memo.book_no == book.book_no).all()
            result['memo_list'] = [
                {
                    'id': memo.id,
                    'memo_content': memo.memo_content,
                    # 'memo_quote': memo.memo_quote,
                    'memo_created_at': memo.memo_created_at
                }
                for memo in memo_instance
            ]

            
            return DataResp(resp_code=200, resp_msg="독서 기록 조회 성공", data=result)
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
            
            new_read = BookRead(
                **payload,
                user_no = user_instance.user_no
            )

            # 독서 기록 내역 없으면 상태를 읽는중으로 전환, 시작 날짜 추가
            if not (
                session.query(BookRead)
                .filter(BookRead.book_no == payload['book_no'], BookRead.user_no == user_instance.user_no)
                .first()
            ) and (payload['book_start_date'] is None):
                new_read.book_start_date = datetime.now()
                book_instance.book_status = 0
                session.add(book_instance)

            # 마지막 페이지 읽으면 상태를 읽음으로 전환, 마지막 날짜 기록
            if (
                new_read.book_current_page == book_instance.book_page
            ):
                new_read.book_end_date = datetime.now()
                book_instance.book_status = 1
                session.add(book_instance)  

            session.add(new_read)
            session.commit()
            
            percent = 0.0

            if  book_instance.book_page > 0:
                percent = (new_read.book_current_page/book_instance.book_page)*100
            
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

    @session_wrapper
    def update_read(self, session, request, payload: GenericPayload, id:int):
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
                book_read_instance := session.query(BookRead).filter(BookRead.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 기록이 없습니다.")
            
            if payload['book_start_date']:
                book_read_instance.book_start_date = payload['book_start_date']
            if payload['book_end_date']:
                book_read_instance.book_end_date = payload['book_end_date']

            session.add(book_read_instance)
            session.commit()
            session.refresh(book_read_instance)
                
            return HttpResp(resp_code=200, resp_msg="독서 기록 수정 성공")
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
    def delete_read(self, session, request, id:int):
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
                book_read_instance := session.query(BookRead).filter(BookRead.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 기록이 없습니다.")

            session.delete(book_read_instance)
            session.commit()
                
            return HttpResp(resp_code=200, resp_msg="책 기록 삭제 성공")
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
    def upload_book_image(self, session, request, book_no:int, file):
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
                book_instance := session.query(Book).filter(Book.book_no == book_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책이 없습니다.")

            # 해당 책에 이미지 있으면
            if (
                image_instance := session.query(BookImage)
                .filter(BookImage.book_no == book_no)
                .first()
            ):  
                # 서버, DB 저장된 이미지 삭제
                os.remove('images/'+image_instance.image_url)
                session.delete(image_instance)
                session.commit()
            
            image_folder = settings.BOOK_IMAGE_DIR

            try:
                os.mkdir(image_folder)
            except FileExistsError:
                pass

            if file.size > (5 * 1024 * 1024):
                return HttpResp(resp_code=400, resp_msg="이미지 용량은 5MB를 초과할 수 없습니다.")
                
            name, ext = os.path.splitext(file.name) # 파일 이름에서 확장자를 분리
            image_name = secrets.token_urlsafe(16) + ext # URL 안전한 임의의 문자열을 생성
            image_path = image_folder + "/" + image_name

            with open(image_path, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            image_url = 'book/' + image_name

            new_image = BookImage(
                book_no = book_no,
                image_name = file.name,
                image_url = image_url
            )

            session.add(new_image)
            session.commit()
            session.refresh(new_image)

            return HttpResp(resp_code=201, resp_msg="이미지 업로드 성공")
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
    def delete_book_image(self, session, request, book_no:int):
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
                book_instance := session.query(Book).filter(Book.book_no == book_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책이 없습니다.")

            # 해당 책에 이미지 있으면
            if not (
                image_instance := session.query(BookImage)
                .filter(BookImage.book_no == book_no)
                .first()
            ):  
                return HttpResp(resp_code=400, resp_msg="일치하는 이미지가 없습니다.")
            
            # 서버, DB 저장된 이미지 삭제
            os.remove('images/'+image_instance.image_url)
            session.delete(image_instance)
            session.commit()

            return HttpResp(resp_code=201, resp_msg="이미지 삭제 성공")
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