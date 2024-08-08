import logging
from datetime import datetime

import jwt
from auths.authorities import TokenTypeEnum
from auths.models import RefreshToken, User
from book import settings
from cores.schema import DataResp


from cores.utils import GenericPayload, session_wrapper


logger = logging.getLogger("django.server")

def jwt_encoder(user, exp_delta, token_type) -> str:
    # JWT 생성
    return jwt.encode(
        {
            "user_no": user.user_no,
            "user_nick": user.user_nick,
            "type": 0 if token_type == "ACCESS" else 1,     # access: 0, refresh: 1
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "exp": datetime.utcnow() + exp_delta,
            "iat": datetime.utcnow(),
            "nbf": datetime.utcnow(),
        },
        key=settings.JWT["JWT_SECRET_KEY"],
        algorithm=settings.JWT["JWT_ALGORITHM"],
    )
    

def jwt_decoder(token) -> dict:
    # JWT 검증
    return jwt.decode(
        token,
        key=settings.JWT["JWT_SECRET_KEY"],
        algorithms=[settings.JWT["JWT_ALGORITHM"]],
    )


class TokenService:
    @session_wrapper
    def generate_pair_token(self, session, user) -> dict:
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(session, user)

        logger.info(
            f"token pair generated for user {user.user_nick} access_token: {access_token} \
            refresh_token: {refresh_token}"
        )
        
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token
        }
    
    def generate_access_token(self, user) -> str:
        """
        access token 발급
        """
        access_token = jwt_encoder(
            user,
            settings.JWT['JWT_ACCESS_EXP_DELTA'],
            "ACCESS"
        )
        return access_token
    
    def generate_refresh_token(self, session, user) -> str:
        """
        refresh token 발급
        """
        refresh_token = jwt_encoder(
            user,
            settings.JWT["JWT_REFRESH_EXP_DELTA"],
            "REFRESH",
        )
        # 이미 DB에 있는 Refresh Token 삭제
        if (
            old_refreshs := session.query(RefreshToken)
            .filter(
                RefreshToken.user_no == user.user_no
            ).all()
        ):
            for old_refresh in old_refreshs:
                session.delete(old_refresh)
                
        # Refresh Token DB 저장
        rt = RefreshToken(
            user_no=user.user_no,
            token=refresh_token,
            exp=datetime.utcnow() + settings.JWT["JWT_REFRESH_EXP_DELTA"],
        )
        session.add(rt)
        session.commit()

        return refresh_token

    def verify_access_token(self, token) -> dict:
        payload = jwt_decoder(token)
        
        if payload['type'] != TokenTypeEnum.ACCESS.value:
            raise jwt.InvalidTokenError
        if payload['exp'] < datetime.utcnow().timestamp():
            raise jwt.ExpiredSignatureError

        return payload

    # @session_wrapper
    def verify_refresh_token(self, token) -> dict:
        """
        REFRESH_TOKEN 테이블에서 토큰 확인
        """
        payload = jwt_decoder(token)

        if payload['type'] != TokenTypeEnum.REFRESH.value:
            raise jwt.InvalidTokenError

        # if not (
        #     refresh_token := session.query(RefreshToken)
        #     .filter(
        #         RefreshToken.user_id == int(payload["user_no"]),
        #         RefreshToken.token == token
        #     ).first()
        # ):
        #     raise jwt.InvalidTokenError

        # if refresh_token.exp < datetime.utcnow():
        #     logger.info(f"Delete refresh token {token}")
        #     session.delete(refresh_token)
        #     session.commit()
        #     raise jwt.ExpiredSignatureError
        
        return payload
    
    # @session_wrapper
    # def revoke_refresh_token(
    #     self, session, user_id, token
    # ) -> None:
    #     """
    #     user_id와 token으로 특정 Refresh token 삭제
    #     """    
    #     session.query(RefreshToken).filter(
    #         RefreshToken.user_id == user_id,
    #         RefreshToken.token == token
    #     ).delete()
    #     session.commit()

    @session_wrapper
    def refresh(self, session, payload: GenericPayload):
        """
        REFRESH_TOKEN 테이블에서 토큰 확인 -> 토큰 리프레시
        """
        try:
        #     token = request.headers.get("Authorization")
        #     if token is not None:
        #         token = token.split(" ")[1]
        #     else:
        #         return HttpResp(resp_code=500, resp_msg="유효하지 않은 토큰 값입니다.")
            
            token_payload = jwt_decoder(payload['refresh_token'])

            if token_payload['type'] != TokenTypeEnum.REFRESH.value:
                raise jwt.InvalidTokenError
            
            # REFRESH_TOKEN 테이블에 없으면 에러
            if not (
            refresh_token := session.query(RefreshToken)
            .filter(
                RefreshToken.user_no == int(token_payload["user_no"]),
                RefreshToken.token == payload['refresh_token']
            ).first()
            ):
                raise jwt.InvalidTokenError
            
            # 만료시 DB에서 삭제 후 에러
            if refresh_token.exp < datetime.utcnow():
                logger.info(f"Delete refresh token {payload['refresh_token']}")
                session.delete(refresh_token)
                session.commit()
                raise jwt.ExpiredSignatureError
            
            
            # access token 발급을 위한 USER 조회
            user_instance = session.query(User).filter(User.user_no == token_payload['user_no']).first()
            
            new_access_token = token_service.generate_access_token(user_instance)

            return DataResp(resp_code=200, resp_msg="토큰 발급 성공", data=new_access_token)
        except Exception as e:
            logger.error(e)
            raise e 

token_service = TokenService()

