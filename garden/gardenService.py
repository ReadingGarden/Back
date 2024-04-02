import logging

from auths.models import User
from auths.tokenService import token_service
from cores.schema import DataResp, HttpResp

from cores.utils import GenericPayload, session_wrapper
from garden.models import Garden, GardenUser


logger = logging.getLogger("django.server")

class GardenService:
    @session_wrapper
    def create_garden(self, session, request, payload: GenericPayload):
        """
        가든 생성
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
            
            # 새로운 가든 객체 생성
            new_garden_dict = {
                **payload,
                "garden_share" : False,
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

            return DataResp(
                resp_code=201, resp_msg="가든 생성 성공", data=payload
            )
        except Exception as e:
            logger.error(e)
            raise e
    pass



garden_service = GardenService()