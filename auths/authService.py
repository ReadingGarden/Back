import hashlib
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from auths.models import User
from cores.schema import DataResp, HttpResp, ServiceError
from cores.utils import GenericPayload, session_wrapper
from auths.tokenService import token_service


logger = logging.getLogger("django.server")

class AuthService:
    # user 로직
    @session_wrapper
    def user_signup(self, session, payload: GenericPayload):
        """
        유저 회원가입
        """
        try:
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
                **payload
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

            return DataResp(resp_code=200, resp_msg="로그인 성공", data=token_pair)
        except VerifyMismatchError as e:
            logger.error(e)
            session.rollback()
            return HttpResp(resp_code=400, resp_msg="아이디 또는 비밀번호가 일치하지 않습니다.")
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
            
            payload = token_service.verify_access_token(token)
            if not(
                user_instance := session.query(User)
                .filter(User.user_no == payload['user_no'])
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 사용자 정보가 없습니다.")
            
            return DataResp(resp_code=200, resp_msg="성공", data=user_instance.as_dict(exclude="user_password"))    
        except Exception as e:
            logger.error(e)
            raise e

        

auth_service = AuthService()