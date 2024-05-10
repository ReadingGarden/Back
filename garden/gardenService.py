import logging

import jwt

from auths.models import User
from auths.tokenService import token_service
from cores.schema import DataResp, HttpResp
from sqlalchemy.orm import aliased

from cores.utils import GenericPayload, session_wrapper
from garden.models import Garden, GardenUser


logger = logging.getLogger("django.server")

class GardenService:
    @session_wrapper
    def create_garden(self, session, request, payload: GenericPayload):
        """
        가든 추가
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
            
            # 가든 개수 가져오기
            garden_user_instance_count = len(session.query(GardenUser).filter(GardenUser.user_no == user_instance.user_no).all())

            if garden_user_instance_count < 5:
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
                    resp_code=201, resp_msg="가든 추가 성공", data=payload
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
        """
        가든 상세 정보 보기
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
            
            if not(
                garden_instance := session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            ):
                return HttpResp(resp_code=400, resp_msg="일치하는 가든 정보가 없습니다.")

            result = garden_instance.as_dict()

            # GardenUser, User join
            garden_members_instance = (
                session.query(GardenUser, User).join(User, User.user_no == GardenUser.user_no)
                .filter(GardenUser.garden_no == garden_no)
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
                        'garden_sign_date': garden_user.garden_sign_date,
                     }
                 )

            result['garden_members'] = garden_members_list
            
            return DataResp(
                resp_code=200, resp_msg="가든 조회 성공", data=result)
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
        """
        가든 List 보기
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

                result.append(
                    {
                        'garden_no': garden.garden_no,
                        'garden_title': garden.garden_title,
                        'garden_info': garden.garden_info,
                        'garden_color': garden.garden_color,
                        'garden_share': garden.garden_share,
                        'garden_members': len(garden_members),
                        'garden_created_at': garden.garden_created_at,
                    }
                )
                
        
            return DataResp(
                resp_code=200, resp_msg="가든 조회 성공", data=result
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
        """
        가든 수정
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
        """
        가든 삭제
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

            session.delete(garden_instance)
            session.delete(garden_user_instance)
            session.commit()
            
            return DataResp(
                resp_code=200, resp_msg="가든 삭제 성공", data={}
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