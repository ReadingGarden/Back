import logging
import os
import secrets
import jwt

from datetime import datetime
from auths.models import User
from auths.tokenService import token_service
from book import settings
from book.models import Book, BookRead
from cores.schema import DataResp, HttpResp

from cores.utils import GenericPayload, session_wrapper
from garden.models import Garden, GardenUser
from memo.models import Memo, MemoImage

logger = logging.getLogger("django.server")

class MemoService:
    @session_wrapper
    def create_memo(self, session, request, payload: GenericPayload):
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
                session.query(Book).filter(Book.book_no == payload['book_no'], Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.")
            
            new_memo = Memo(
                **payload,
                user_no = user_instance.user_no
            )

            session.add(new_memo)
            session.commit()
            session.refresh(new_memo)

            return DataResp(resp_code=201, resp_msg="메모 추가 성공", data={
                'id': new_memo.id
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
    def update_memo(self, session, request, payload: GenericPayload, id:int):
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
                memo_instance := session.query(Memo).filter(Memo.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 메모가 없습니다.")
            
            if not (
                session.query(Book).filter(Book.book_no == payload['book_no'], Book.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 책 정보가 없습니다.") 

            memo_instance.book_no = payload['book_no']
            memo_instance.memo_content = payload['memo_content']
            # memo_instance.memo_quote = payload['memo_quote']
            
            session.add(memo_instance)
            session.commit()
            session.refresh(memo_instance)
                
            return HttpResp(resp_code=200, resp_msg="메모 수정 성공")
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
    def delete_memo(self, session, request, id:int):
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
                memo_instance := session.query(Memo).filter(Memo.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 메모가 없습니다.")
            
            if (
                image_instance := session.query(MemoImage)
                .filter(MemoImage.memo_no == id)
                .first()
            ):
                # 서버, DB 저장된 이미지 삭제
                os.remove('images/'+image_instance.image_url)    
                session.delete(image_instance)
                session.commit()
            
            session.delete(memo_instance)
            session.commit()
            
            return HttpResp(resp_code=200, resp_msg="메모 삭제 성공")
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
    def get_memo(self, session, request):
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
            
            # Memo, Book join
            memo_book_instance = (
                session.query(Memo, Book)
                .join(Book, Book.book_no == Memo.book_no)
                .filter(Memo.user_no == user_instance.user_no)
                .order_by(Memo.memo_like.desc(), Memo.memo_created_at.desc())
                .all()
                )

            result = [                
                {
                    'id': memo.id,
                    'book_no': memo.book_no,
                    'book_title': book.book_title,
                    'book_author': book.book_author,
                    'book_image_url': book.book_image_url,
                    'memo_content': memo.memo_content,
                    # 'memo_quote': memo.memo_quote,
                    'memo_like': memo.memo_like,
                    'image_url': (
                        (image_instance.image_url if image_instance else '')
                        if (image_instance := session.query(MemoImage)
                            .filter(MemoImage.memo_no == memo.id)
                            .first())
                        else None
                    ),
                    'memo_created_at': memo.memo_created_at
                }
                for memo, book in memo_book_instance
            ]

            return DataResp(resp_code=200, resp_msg="메모 리스트 조회 성공", data=result)
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
    def get_memo_detail(self, session, request, id:int):
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
                # Memo, Book join
                memo_book_instance := session.query(Memo, Book).join(Book, Book.book_no == Memo.book_no).filter(Memo.user_no == user_instance.user_no).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 메모가 없습니다.")
            
            memo, book = memo_book_instance

            image_instance = session.query(MemoImage).filter(MemoImage.memo_no == id).first()
            image_url = image_instance.image_url if image_instance else None

            result = {
                    'id': memo.id,
                    'book_no': memo.book_no,
                    'book_title': book.book_title,
                    'book_author': book.book_author,
                    'book_publisher': book.book_publisher,
                    'memo_content': memo.memo_content,
                    # 'memo_quote': memo.memo_quote,
                    'image_url': image_url,
                    'memo_created_at': memo.memo_created_at
            }
            
            return DataResp(resp_code=200, resp_msg="메모 상세 조회 성공", data=result)
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
    def like_memo(self, session, request, id:int):
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
                memo_instance := session.query(Memo).filter(Memo.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 메모가 없습니다.")
            
            memo_instance.memo_like = not memo_instance.memo_like
            
            session.add(memo_instance)
            session.commit()
            session.refresh(memo_instance)
            
            return HttpResp(resp_code=200, resp_msg="메모 즐겨찾기 추가/해제")
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
    def upload_memo_image(self, session, request, id:int, file):
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
                memo_instance := session.query(Memo).filter(Memo.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 메모가 없습니다.")

            # 해당 메모에 이미지 있으면
            if (
                image_instance := session.query(MemoImage)
                .filter(MemoImage.memo_no == id)
                .first()
            ):  
                # 서버, DB 저장된 이미지 삭제
                os.remove('images/'+image_instance.image_url)
                session.delete(image_instance)
                session.commit()
            
            image_folder = settings.MEMO_IMAGE_DIR

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

            image_url = 'memo/' + image_name

            new_image = MemoImage(
                memo_no = id,
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
    def delete_memo_image(self, session, request, id:int):
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
                memo_instance := session.query(Memo).filter(Memo.id == id).first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 메모가 없습니다.")

            # 해당 메모에 이미지 있으면
            if not (
                image_instance := session.query(MemoImage)
                .filter(MemoImage.memo_no == id)
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

memo_service = MemoService()