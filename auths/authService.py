import logging

from argon2.exceptions import VerifyMismatchError
from django.utils import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import jwt
from tzlocal import get_localzone

from auths.models import RefreshToken, User
from book import settings
from book.models import Book
from cores.schema import DataResp, HttpResp, ServiceError
from cores.utils import GenericPayload, hash_password, send_email, session_wrapper, generate_random_string, generate_random_nick, reset_auth_number, verify_password
from auths.tokenService import token_service
from garden.models import Garden, GardenUser


logger = logging.getLogger("django.server")

# 스케쥴러 등록
scheduler = BackgroundScheduler()
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SQLALCHEMY_DATABASE_URI)
}
executors = {
  'default': ThreadPoolExecutor(20),
  'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
  'coalesce': False,
  'max_instances': 3
}
local_timezone = get_localzone()
scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=local_timezone)

scheduler.start()

class AuthService:
    @session_wrapper
    def create_user(self, session, payload: GenericPayload):
        try:
            if payload['user_social_id']:
                # 소셜 가입 중복 확인
                if (
                    session.query(User)
                    .filter(User.user_social_id == payload["user_social_id"], User.user_social_type == payload["user_social_type"])
                    .first()
                ):
                    return HttpResp(resp_code=409, resp_msg="소셜 아이디 중복")
            else:
                # 이메일 중복 확인
                if (
                    session.query(User)
                    .filter(User.user_email == payload["user_email"])
                    .first()
                ):
                    return HttpResp(resp_code=409, resp_msg="이메일 중복")
            
            if payload['user_password']:
                # 비밀번호 암호화
                hashed_password = hash_password(payload['user_password'])
                payload["user_password"] = hashed_password
                
            # 새로운 유저 객체 생성
            new_user = User(
                **payload,
                user_nick = generate_random_nick()
            )

            # 세션에 추가
            session.add(new_user)
            # DB에 저장
            session.commit()
            session.refresh(new_user)
            
            # 새로운 가든 객체 생성
            new_garden_dict = {
                "garden_title" : f'{new_user.user_nick}의 가든',
                "garden_info" : '독서가든에 오신걸 환영합니다☺️',
                "garden_color" : 'green',
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
                "user_no" : new_user.user_no,
                "garden_leader" : True,
                "garden_main": True
            }
            new_garden_user = GardenUser(
                **new_garden_user_dict
            )
            
            session.add(new_garden_user)
            session.commit()
            session.refresh(new_garden_user)

            

            return DataResp(
                resp_code=201, resp_msg="회원가입 성공", data={"user_no": new_user.user_no}
            )
        except Exception as e:
            logger.error(e)
            raise e

    @session_wrapper
    def user_login(self, session, payload: GenericPayload) -> dict:
        try:
            if payload['user_social_id']:
                if not (
                    user_instance := session.query(User)
                    .filter(User.user_social_id == payload['user_social_id'], User.user_social_type == payload['user_social_type'])
                    .first()
                ):
                    return HttpResp(resp_code=400, resp_msg="등록되지 않은 소셜입니다")
            else:
                if not (
                    user_instance := session.query(User)
                    .filter(User.user_email == payload['user_email'])
                    .first()
                ):
                    return HttpResp(resp_code=400, resp_msg="등록되지 않은 이메일 주소입니다.")
                # 비밀번호 암호화 검증
                if not (
                    verify_password(payload['user_password'], user_instance.user_password)
                ):
                    return HttpResp(resp_code=400, resp_msg="비밀번호가 일치하지 않습니다.")
                
            # 토큰 발급
            token_pair = token_service.generate_pair_token(user_instance)

            # fcm 토큰 저장
            user_instance.user_fcm = payload['user_fcm']

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)

            return DataResp(resp_code=200, resp_msg="로그인 성공", data=token_pair)
        except VerifyMismatchError as e:
            logger.error(e)
            session.rollback()
            return HttpResp(resp_code=400, resp_msg="아이디 또는 비밀번호가 일치하지 않습니다.")
        except Exception as e:
            logger.error(e)
            raise e
        
    @session_wrapper
    def user_logout(self, session, request):
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
            

            # Refresh Token 삭제
            refresh_token = session.query(RefreshToken).filter(RefreshToken.user_no == user_instance.user_no).first()

            session.delete(refresh_token)

            # FCM 삭제
            user_instance.user_fcm = ''

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)

            
            # token_service.revoke_refresh_token(token)

            return DataResp(resp_code=200, resp_msg="로그아웃 성공", data={})
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
    def refresh(self, session, payload: GenericPayload):
        try:
        #     token = request.headers.get("Authorization")
        #     if token is not None:
        #         token = token.split(" ")[1]
        #     else:
        #         return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = token_service.verify_refresh_token(payload['refresh_token'])
            user_instance = session.query(User).filter(User.user_no == token_payload['user_no']).first()
            
            new_token = token_service.generate_access_token(user_instance)

            return DataResp(resp_code=200, resp_msg="토큰 발급 성공", data=new_token)
        except Exception as e:
            logger.error(e)
            raise e 
        
    @session_wrapper
    def user_delete(self, session, request):
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
            
            refresh_token = session.query(RefreshToken).filter(RefreshToken.user_no == user_instance.user_no).first()
            
            session.delete(user_instance)
            session.delete(refresh_token)
            session.commit()
        
            return DataResp(resp_code=200, resp_msg="회원 탈퇴 성공", data={})
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
    def user_find_password(
        self, session, payload: GenericPayload
    ):
        try:
            if not (
                user_instance := session.query(User)
                .filter(User.user_email == payload['user_email'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="등록되지 않은 이메일 주소입니다.")
            try:
                auth_number = generate_random_string(5)
                send_email(email=payload['user_email'], title='test', content=auth_number)
            except:
                return HttpResp(resp_code=500, resp_msg="메일 전송 실패")
            
            reset_date = timezone.localtime(timezone.now()) + timezone.timedelta(minutes=5)
            # logger.info(f"reset_date {reset_date.year, reset_date.month, reset_date.day, reset_date.hour, reset_date.minute}")
            scheduler.add_job(
                func=reset_auth_number,
                args=[user_instance],
                trigger=CronTrigger(
                     year=str(reset_date.year),
                     month=str(reset_date.month),
                     day=str(reset_date.day),
                     hour=str(reset_date.hour),
                     minute=str(reset_date.minute),
                ),
            )
            
            # db에 인증번호 저장
            user_instance.user_auth_number = auth_number

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
    
            return DataResp(resp_code=200, resp_msg="메일이 발송되었습니다. 확인해주세요.", data={})    
        except Exception as e:
            logger.error(e)
            raise e

    @session_wrapper
    def user_auth_check(
        self, session, payload: GenericPayload
    ):
        try:
            user_instance = session.query(User).filter(User.user_email == payload['user_email']).first()

            if user_instance.user_auth_number == payload['auth_number']:
                 return DataResp(resp_code=200, resp_msg="인증 성공", data={})
            else:
                return HttpResp(resp_code=400, resp_msg="인증번호 불일치")
        except Exception as e:
            logger.error(e)
            raise e
        
    @session_wrapper
    def user_update_password_no_token(
        self, session, payload: GenericPayload
    ):
        """
        유저 비밀번호 변경 (토큰 X)
        """
        try:
            user_instance = session.query(User).filter(User.user_email == payload['user_email']).first()
            
            # 비밀번호 암호화
            hashed_password = hash_password(payload['user_password'])
            user_instance.user_password = hashed_password

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
            return HttpResp(resp_code=200, resp_msg="비밀번호 변경 성공")
        except Exception as e:
            logger.error(e)
            raise e
        
    @session_wrapper
    def user_update_password(
        self, session, request, payload: GenericPayload
    ):
        """
        유저 비밀번호 변경 (토큰 O)
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
            
            hashed_password = hash_password(payload['user_password'])
            user_instance.user_password = hashed_password

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
            return HttpResp(resp_code=200, resp_msg="비밀번호 변경 성공")
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
    def get_user(
        self, session, request
    ):
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
            
            # Garden 개수
            garden_count = (
                len(session.query(GardenUser).filter(GardenUser.user_no == user_instance.user_no).all())
            )

            book_query = session.query(Book).filter(Book.user_no == user_instance.user_no)
            read_book_count = len(book_query.filter(Book.book_status == 1).all())
            like_book_count = len(book_query.filter(Book.book_status == 2).all())

            result = {
                "user_no": user_instance.user_no,
                "user_nick": user_instance.user_nick,
                "user_email": user_instance.user_email,
                # "user_fcm": "string",
                # "user_social_id": "string",
                "user_social_type": user_instance.user_social_type,
                "user_image": user_instance.user_image,
                "user_created_at": user_instance.user_created_at,
                "garden_count": garden_count,
                "read_book_count": read_book_count,
                "like_book_count": like_book_count,
            }

            
            
            return DataResp(resp_code=200, resp_msg="조회 성공", data=result)
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
    def update_user(
        self, session, request, payload: GenericPayload
    ):
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
            
            # db에 프로필 update
            if (payload['user_nick']):
                user_instance.user_nick = payload['user_nick']
            else:
                user_instance.user_image = payload['user_image']

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
            
            return DataResp(resp_code=200, resp_msg="프로필 변경 성공", data=user_instance.as_dict(exclude="user_password"))
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')    
        except Exception as e:
            logger.error(e)
            raise e
        
        

    
auth_service = AuthService()