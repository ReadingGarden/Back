import logging
import jwt

from django.http import HttpRequest
from jwt import ExpiredSignatureError

from ninja.security import HttpBearer

from auths.tokenService import token_service
from book import settings

logger = logging.getLogger("django.server")

class UserAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        try:
            token_service.verify_access_token(token)
            return token
        except ExpiredSignatureError:
            logger.error(f"Expired token supplied to {request.path}")
            return {'error': ExpiredSignatureError}
            # raise ExpiredSignatureError
        
