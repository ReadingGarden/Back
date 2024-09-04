import logging
import jwt

from auths.models import User
from auths.tokenService import token_service
from cores.schema import HttpResp
from cores.utils import GenericPayload, session_wrapper


logger = logging.getLogger("django.server")

class PushService:
    # @session_wrapper
    # def create_push(self, session, payload: GenericPayload):
    #     try:
    #         return HttpResp(resp)
    #         pass
    #     except (
    #         jwt.ExpiredSignatureError,
    #         jwt.InvalidTokenError,
    #         jwt.DecodeError
    #     ) as e:
    #         return HttpResp(resp_code=401, resp_msg=f'{e}')        
    #     except Exception as e:
    #         logger.error(e)
    #         raise e
        

    @session_wrapper
    def update_push(self, session, request, payload: GenericPayload):
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
            
            return HttpResp(resp_code=200, resp_msg="푸시 알림 수정 성공")
            pass
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e


push_service = PushService()