import logging
import os
import jwt

from sqlalchemy import asc, desc
from auths.models import User
from auths.tokenService import token_service
from book.models import Book, BookImage, BookRead
from cores.schema import DataResp, HttpResp
from sqlalchemy.orm import aliased

from cores.utils import GenericPayload, session_wrapper
from garden.models import Garden, GardenUser
from memo.models import Memo, MemoImage


logger = logging.getLogger("django.server")

class GardenService:
    @session_wrapper
    def create_garden(self, session, request, payload: GenericPayload):
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
            
            # 가든 개수 가져오기
            garden_user_instance_count = len(session.query(GardenUser).filter(GardenUser.user_no == user_instance.user_no).all())

            if garden_user_instance_count < 5:
                # 새로운 가든 객체 생성
                new_garden_dict = {
                    **payload,
                }
                new_garden = Garden(
                    **new_garden_dict
                )
                session.add(new_garden)
                session.commit()
                session.refresh(new_garden)

                # 새로운 가든-유저 객체 생성
                new_garden_user_dict = {
                    "garden_no" : new_garden.garden_no,
                    "user_no" : user_instance.user_no,
                    "garden_leader" : True,
                }
                new_garden_user = GardenUser(
                    **new_garden_user_dict
                )
                session.add(new_garden_user)
                session.commit()
                session.refresh(new_garden_user)

                data = {
                    **payload
                }
                data['garden_no'] = new_garden.garden_no

                return DataResp(
                    resp_code=201, resp_msg="가든 추가 성공", data=data
                )
            
            else:
                return HttpResp(resp_code=403, resp_msg="가든 생성 개수 초과")
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
    def get_garden_detail(self, session, request, garden_no: int):
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
            
            if not(
                garden_instance := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")
            
            result = garden_instance.as_dict()
            
            # Book 가져오기
            book_instance = (
                session.query(Book)
                .filter(Book.garden_no == garden_no)
                .all()
            )
            
            book_list = []

            #TODO - 나무 타입
            for book in book_instance:
                percent = 0
                if (
                    book_read_instance := 
                    session.query(BookRead)
                    .filter(BookRead.book_no == book.book_no)
                    .order_by(desc(BookRead.created_at))
                    .first()
                ):
                    percent = (book_read_instance.book_current_page/book.book_page)*100
                
                book_list.append({
                        'book_no': book.book_no,
                        'book_isbn': book.book_isbn,
                        'book_title': book.book_title,
                        'book_author': book.book_author,
                        'book_publisher': book.book_publisher,
                        'book_image_url': book.book_image_url,
                        'book_status': book.book_status,
                        'percent': percent,
                        'user_no': book.user_no,
                        'book_page': book.book_page
                        })

            result['book_list'] = book_list

            #TODO: - 정렬하기 
            # GardenUser, User join
            garden_members_instance = (
                session.query(GardenUser, User).join(User, User.user_no == GardenUser.user_no)
                .filter(GardenUser.garden_no == garden_no)
                .order_by(
                    GardenUser.garden_leader.desc(),
                    GardenUser.garden_sign_date.asc()
                )
                .all()
            )

            garden_members_list = []
            # 각 결과 항목을 딕셔너리로 변환하여 리스트에 추가
            for garden_user, user in garden_members_instance:
                 garden_members_list.append(
                     {
                        'user_no': user.user_no,
                        'user_nick': user.user_nick,
                        'user_image': user.user_image,
                        'garden_leader': garden_user.garden_leader,
                        'garden_sign_date': garden_user.garden_sign_date,
                     }
                 )

            result['garden_members'] = garden_members_list

            return DataResp(
                resp_code=200, resp_msg="가든 상세 조회 성공", data=result)
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
    def get_garden(self, session, request):
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
            
            result = []

            # GardenUser 클래스에 대한 별칭 생성
            garden_user_alias = aliased(GardenUser)
            # Garden, GardenUser join
            gardens = (
                session.query(Garden)
                .join(
                garden_user_alias, garden_user_alias.garden_no == Garden.garden_no
            )
            .filter(garden_user_alias.user_no == user_instance.user_no)
            .all()
            )

            for garden in gardens:
                # garden 멤버 가져오기
                garden_members = session.query(garden_user_alias).filter(garden_user_alias.garden_no == garden.garden_no).all()

                # Book 가져오기
                book_instance_count = len(session.query(Book).filter(Book.garden_no ==garden.garden_no).all())
                

                result.append(
                    {
                        'garden_no': garden.garden_no,
                        'garden_title': garden.garden_title,
                        'garden_info': garden.garden_info,
                        'garden_color': garden.garden_color,
                        'garden_members': len(garden_members),
                        'book_count': book_instance_count,
                        'garden_created_at': garden.garden_created_at,
                    }
                )
                
        
            return DataResp(
                resp_code=200, resp_msg="가든 리스트 조회 성공", data=result
            )
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
    def update_garden(self, session, request, payload: GenericPayload, garden_no: int):
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
            
            if not(
                garden_instacne := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")
            
            # garden update
            garden_instacne.garden_title = payload['garden_title']
            garden_instacne.garden_info = payload['garden_info']
            garden_instacne.garden_color = payload['garden_color']

            session.add(garden_instacne)
            session.commit()
            session.refresh(garden_instacne)
            
            return DataResp(
                resp_code=200, resp_msg="가든 수정 성공", data={}
            )
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
    def delete_garden(self, session, request, garden_no: int):
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
            
            if not(
                garden_instance := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")
            
            # 가든이 1개 이하면
            if not (
                len(session.query(GardenUser)
                .filter(GardenUser.user_no == user_instance.user_no)
                .all()) > 1
            ):
                return HttpResp(resp_code=403, resp_msg="가든 삭제 불가")
            
            garden_user_instance = session.query(GardenUser).filter(GardenUser.garden_no == garden_no, GardenUser.user_no == user_instance.user_no).first()

            # 가든에 있는 책 삭제
            book_instance = session.query(Book).filter(Book.garden_no == garden_no, Book.user_no == user_instance.user_no).all()
            for book in book_instance:
                # 책 이미지 삭제
                book_image_instance = session.query(BookImage).filter(BookImage.book_no == book.book_no).first()
                if book_image_instance:
                    try:
                        os.remove('images/'+book_image_instance.image_url)
                        session.delete(book_image_instance)
                    except FileNotFoundError:
                        pass
                session.delete(book)
                # 메모 삭제
                memo_instance = session.query(Memo).filter(Memo.book_no == book.book_no).all()
                for memo in memo_instance:
                    memo_image_instance = session.query(MemoImage).filter(MemoImage.memo_no == memo.id).first()
                    if memo_image_instance:
                        try:
                            os.remove('images/'+memo_image_instance.image_url)
                            session.delete(memo_image_instance)
                        except FileNotFoundError:
                            pass
                    session.delete(memo)

            session.delete(garden_instance)
            session.delete(garden_user_instance)
            session.commit()
            
            return HttpResp(
                resp_code=200, resp_msg="가든 삭제 성공"
            )
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
    def delete_to_garden(self, session, request, garden_no: int, to_garden_no:int):
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
            
            if not(
                garden_instance := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")
            
            # 가든이 1개 이하면
            if not (
                len(session.query(GardenUser)
                .filter(GardenUser.user_no == user_instance.user_no)
                .all()) > 1
            ):
                return HttpResp(resp_code=403, resp_msg="가든 삭제 불가")
            
            garden_user_instance = session.query(GardenUser).filter(GardenUser.garden_no == garden_no, GardenUser.user_no == user_instance.user_no).first()

            # 책 옮기기
            book_instance = session.query(Book).filter(Book.garden_no == garden_no, Book.user_no == user_instance.user_no).all()
            for book in book_instance:
                book.garden_no = to_garden_no
                session.add(book)
                
            session.delete(garden_instance)
            session.delete(garden_user_instance)
            session.commit()
            
            return HttpResp(
                resp_code=200, resp_msg="가든 삭제(책 이동) 성공"
            )
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
    def delete_garden_member(self, session, request, garden_no: int):
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
            
            if not(
                garden_instance := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")            
            
            garden_user_instance = session.query(GardenUser).filter(GardenUser.garden_no == garden_no, GardenUser.user_no == user_instance.user_no).first()

            # 현재 대표 -> 위임
            if garden_user_instance.garden_leader:
                garden_user_instance2 = session.query(GardenUser).filter(GardenUser.garden_no == garden_no, GardenUser.user_no != user_instance.user_no).first()
                
                garden_user_instance2.garden_leader = True

                session.add(garden_user_instance2)
                session.commit()
                session.refresh(garden_user_instance2)

            session.delete(garden_user_instance)
            session.commit()
            
            return HttpResp(
                resp_code=200, resp_msg="가든 탈퇴 성공"
            )
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
    def update_garden_leader(self, session, request, garden_no: int, user_no:int):
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
            
            if not(
                garden_instance := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")            
            
            garden_user_instance = session.query(GardenUser).filter(GardenUser.garden_no == garden_no, GardenUser.user_no == user_instance.user_no).first()

            # 현재 대표 -> 위임
            if garden_user_instance.garden_leader:
                garden_user_instance2 = session.query(GardenUser).filter(GardenUser.garden_no == garden_no, GardenUser.user_no == user_no).order_by(asc(GardenUser.garden_sign_date)).first()
                
                garden_user_instance.garden_leader = False
                garden_user_instance2.garden_leader = True

                session.add(garden_user_instance2)
                session.commit()
                session.refresh(garden_user_instance2)
            
            return HttpResp(
                resp_code=200, resp_msg="가든 멤버 변경 성공"
            )
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')    
        except Exception as e:
            logger.error(e)
            raise e



garden_service = GardenService()