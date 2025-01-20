from datetime import datetime
import json
import logging
import jwt
import firebase_admin

from firebase_admin import messaging
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import requests

from auths.models import User
from auths.tokenService import token_service
from book import settings
from cores.schema import DataResp, HttpResp
from cores.utils import GenericPayload, session_wrapper
from garden.models import Garden
from push.models import Push


logger = logging.getLogger("django.server")

class PushService:
    @session_wrapper
    def get_push(self, session, request):
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
            
            push_instance = session.query(Push).filter(Push.user_no == user_instance.user_no).first()

            result = push_instance.to_dict()
            
            return DataResp(resp_code=200, resp_msg="푸시 알림 조회 성공", data=result)
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
            
            push_instance = session.query(Push).filter(Push.user_no == user_instance.user_no).first()

            if payload['push_app_ok'] is not None:
                push_instance.push_app_ok = payload['push_app_ok']
            if payload['push_book_ok']is not None:
                push_instance.push_book_ok = payload['push_book_ok']
            if payload['push_time']:
                push_instance.push_time = payload['push_time']

            session.add(push_instance)
            session.commit()
            session.refresh(push_instance)
            
            return HttpResp(resp_code=200, resp_msg="푸시 알림 수정 성공")
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError
        ) as e:
            return HttpResp(resp_code=401, resp_msg=f'{e}')        
        except Exception as e:
            logger.error(e)
            raise e
        
    # Firebase 서비스 계정을 사용하여 OAuth2 액세스 토큰을 생성
    def get_access_token(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.SERVICE_ACCOUNT_FILE, scopes=settings.SCOPES
            )
            # 인증 토큰을 갱신
            credentials.refresh(Request())
            access_token = credentials.token
            if not access_token:
                raise Exception("Failed to get access token")
            return access_token
        except Exception as e:
            logger.error(e)
        raise e

    # FCM 메시지를 단일 토큰으로 전송
    def send_fcm(self, token, title, body, data):
        url = f"https://fcm.googleapis.com/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send"
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json",
        }
        # 메시지 요청 데이터
        message = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body,
                },
                "data": data,
            }
        }


        # HTTP 요청 전송
        response = requests.post(url, headers=headers, data=json.dumps(message))
        return response.json() if response.status_code == 200 else response.text

    # 여러 토큰에 FCM 메시지를 전송
    def send_multicast_fcm(self, tokens, title, body, data):
        results = []
        for token in tokens:
            if token:  # 유효한 토큰만 전송
                result = self.send_fcm(token, title, body, data)
                results.append(result)
        return results
    
    
    @session_wrapper
    def send_new_member_push(self, session, user_no, garden_no):
        try:
            # User, Push join
            user_push_instance = (
                session.query(User, Push)
                .join(Push, Push.user_no == User.user_no)
                .filter(User.user_no == user_no, Push.push_app_ok == True).
                all()
            )

            tokens = []

            for user, push in user_push_instance:
                tokens.append(user.user_fcm)
                        

            # 빈 값 제거 및 유효한 토큰 필터링
            tokens = [token for token in tokens if token and isinstance(token, str) and token.strip()]

            results = []

            # 해당 가든 가져오기
            garden_instance = (
                session.query(Garden)
                .filter(Garden.garden_no == garden_no)
                .first()
            )

            # 멀티캐스트 FCM 메시지 전송
            if tokens:
                title = 'NEW 가드너 등장🧑‍🌾'
                body =  f'{garden_instance.garden_title}에 새로운 멤버가 들어왔어요. 함께 책을 읽어 가든을 채워주세요'
                data = {"garden_no": str(garden_no)}
                results = self.send_multicast_fcm(tokens, title, body, data)

                return DataResp(resp_code=200, resp_msg="새 멤버 알림 푸시 전송 성공" , data=results)
        except Exception as e:
            logger.error(e)
            raise e
    

    @session_wrapper
    def send_book_push(self, session):
        try:
            # User, Push join
            user_push_instance = (
                session.query(User, Push)
                .join(Push, Push.user_no == User.user_no)
                .filter(Push.push_book_ok == True).
                all()
            )

            tokens = []

            for user, push in user_push_instance:
                # 현재 시간을 "HH:MM" 형식으로 가져오기
                current_time = datetime.now().strftime("%H:%M")
                # push.push_time에서 시간만 추출
                if push.push_time is not None:
                    push_time_str = push.push_time.strftime("%H:%M")
                    if push_time_str == current_time:
                        tokens.append(user.user_fcm)

            # 빈 값 제거 및 유효한 토큰 필터링
            tokens = [token for token in tokens if token and isinstance(token, str) and token.strip()]

            results = []

            # 멀티캐스트 FCM 메시지 전송
            if tokens:
                title = '지금은 물 주는 시간🪴'
                body =  '책 어디까지 읽으셨나요? 독서가든에서 기록해보세요!'
                results = self.send_multicast_fcm(tokens, title, body, {})

            return DataResp(resp_code=200, resp_msg="독서 알림 푸시 전송 성공" , data=results)
        except Exception as e:
            logger.error(e)
            raise e
        
    @session_wrapper
    def send_notice_push(self, session, content: str):
        try:
            # User, Push join
            user_push_instance = (
                session.query(User, Push)
                .join(Push, Push.user_no == User.user_no)
                .filter(Push.push_app_ok == True).
                all()
            )

            tokens = []

            for user, push in user_push_instance:
                        tokens.append(user.user_fcm)

            # 빈 값 제거 및 유효한 토큰 필터링
            tokens = [token for token in tokens if token and isinstance(token, str) and token.strip()]

            results = []

            # 멀티캐스트 FCM 메시지 전송
            if tokens:
                title = '독서가든'
                body =  content
                results = self.send_multicast_fcm(tokens, title, body, {})

            return DataResp(resp_code=200, resp_msg="공지사항 푸시 전송 성공" , data=results)
        except Exception as e:
            logger.error(e)
            raise e

        
push_service = PushService()