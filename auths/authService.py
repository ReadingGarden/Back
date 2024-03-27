from datetime import timedelta
import hashlib
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.base import JobLookupError
from tzlocal import get_localzone

from auths.models import User
from book import settings
from cores.schema import DataResp, HttpResp, ServiceError
from cores.utils import GenericPayload, send_email, session_wrapper, generate_random_string, generate_random_nick, reset_auth_number
from auths.tokenService import token_service


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
    # user 로직
    @session_wrapper
    def create_user(self, session, payload: GenericPayload):
        """
        유저 회원가입
        """
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
                
            #TODO 비밀번호 암호화
            # 비밀번호 암호화
            # password_md5 = hashlib.md(form["user_password"].encode().hexdigest().upper())
            # password_hash = hashlib.sha512(password_md5.encode()).hexdigest()

            # form["user_password"] = password_hash
                
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

            return DataResp(
                resp_code=200, resp_msg="회원가입 성공", data={"user_no": new_user.user_no}
            )
        except Exception as e:
            logger.error(e)
            raise e

    @session_wrapper
    def user_login(self, session, payload: GenericPayload) -> dict:
        """
        유저 로그인
        """
        try:
            ph = PasswordHasher()
            # user_email, user_password = payload['user_email'], payload['user_password']
            if payload['user_social_id']:
                if not (
                    user_instance := session.query(User)
                    .filter(User.user_social_id == payload['user_social_id'], User.user_social_type == payload['user_social_type'])
                    .first()
                ):
                    return HttpResp(resp_code=400, resp_msg="존재하지 않는 소셜")
            else:
                if not (
                    user_instance := session.query(User)
                    .filter(User.user_email == payload['user_email'])
                    .first()
                ):
                    return HttpResp(resp_code=400, resp_msg="존재하지 않는 이메일")
                if not (
                    user_instance.user_password == payload['user_password']
                ):
                    return HttpResp(resp_code=400, resp_msg="비밀번호가 일치하지 않습니다.")
            #TODO - 비밀번호 암호화
            # ph.verify(user_instance.user_password, payload['user_password'])
            
            # 토큰 발급
            token_pair = token_service.generate_pair_token(user_instance)

            logger.info(f"유우우우우우우저{user_instance}")

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
        """
        유저 로그아웃
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
            
            # db에 프로필 update
            user_instance.user_fcm = None

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
        
            return DataResp(resp_code=200, resp_msg="로그아웃 성공", data={})
        except Exception as e:
            logger.error(e)
            raise e
        
    @session_wrapper
    def user_delete(self, session, request):
        """
        유저 회원 탈퇴
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
            
            # TODO: - 로직 변경!!!
            session.delete(user_instance)
            session.commit()
            session.refresh(user_instance)
        
            return DataResp(resp_code=200, resp_msg="회원 탈퇴 성공", data={})
        except Exception as e:
            logger.error(e)
            raise e

    @session_wrapper
    def user_find_password(
        self, session, payload: GenericPayload
    ):
        """
        유저 비밀번호 인증 메일 전송
        """
        try:
            if not (
                user_instance := session.query(User)
                .filter(User.user_email == payload['user_email'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="등록되지 않은 이메일 주소입니다")
            try:
                auth_number = generate_random_string(5)
                send_email(email=payload['user_email'], title='test', content=auth_number)
            except:
                return HttpResp(resp_code=403, resp_msg="메일 전송 실패")
            
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
    
            return DataResp(resp_code=200, resp_msg="메일 전송 성공", data={})    
        except Exception as e:
            logger.error(e)
            raise e

    @session_wrapper
    def user_auth_check(
        self, session, payload: GenericPayload
    ):
        """
        유저 비밀번호 인증 확인
        """
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
    def user_update_password(
        self, session, payload: GenericPayload
    ):
        pass

    @session_wrapper
    def get_user(
        self, session, request
    ):
        """
        유저 조회
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
            
            return DataResp(resp_code=200, resp_msg="성공", data=user_instance.as_dict(exclude="user_password"))
        except IndexError:
            logger.error("Invalid Index")
            return HttpResp(resp_code=500, resp_msg=str(e))
        except ObjectDoesNotExist as e:
            logger.error("Object Does Not Exist")
            return HttpResp(resp_code=500, resp_msg=str(e))    
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
            user_instance.user_nick = payload['user_nick']
            user_instance.user_image = payload['user_image']

            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
            
            return DataResp(resp_code=200, resp_msg="성공", data=user_instance.as_dict(exclude="user_password"))
        
        except IndexError:
            logger.error("Invalid Index")
            return HttpResp(resp_code=500, resp_msg=str(e))
        except ObjectDoesNotExist as e:
            logger.error("Object Does Not Exist")
            return HttpResp(resp_code=500, resp_msg=str(e))
        except Exception as e:
            logger.error(e)
            raise e
        
        

    
auth_service = AuthService()