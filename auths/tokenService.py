import logging
from datetime import datetime

import jwt
from auths.authorities import TokenTypeEnum
from auths.models import RefreshToken
from book import settings


from cores.utils import session_wrapper


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
        # TODO - 리프레시 토큰 DB 저장
        # rt = RefreshToken(
        #     user_no=user.user_no,
        #     token=refresh_token,
        #     exp=datetime.utcnow() + settings.JWT["JWT_REFRESH_EXP_DELTA"],
        # )
        # session.add(rt)
        # session.commit()

        return refresh_token

    def verify_access_token(self, token) -> dict:
        payload = jwt_decoder(token)
        
        if payload['type'] != TokenTypeEnum.ACCESS.value:
            raise jwt.InvalidTokenError
        if payload['exp'] < datetime.utcnow().timestamp():
            raise jwt.ExpiredSignatureError

        return payload

    @session_wrapper
    def verify_refresh_token(self, session, token) -> dict:
        """
        refresh_tokens 테이블에서 토큰 확인
        """
        payload = jwt_decoder(token)

        if payload['type'] != TokenTypeEnum.REFRESH.value:
            raise jwt.InvalidTokenError

        if not (
            refresh_token := session.query(RefreshToken)
            .filter(
                RefreshToken.user_id == int(payload["user_no"]),
                RefreshToken.token == token
            ).first()
        ):
            raise jwt.InvalidTokenError

        if refresh_token.exp < datetime.utcnow():
            logger.info(f"Delete refresh token {token}")
            session.delete(refresh_token)
            session.commit()
            raise jwt.ExpiredSignatureError
        
        return payload


token_service = TokenService()

