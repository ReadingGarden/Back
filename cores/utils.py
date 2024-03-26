from email.message import EmailMessage
from functools import wraps
import random
import smtplib
import string
from typing import TypeVar

import logging
import jwt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from book import settings
from cores.schema import HttpResp

GenericPayload = TypeVar("GenericPayload")
logger = logging.getLogger("django.server")


engin = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(
    autocommit=False, autoflush=False, bind=engin, expire_on_commit=False
)
SessionLocal = scoped_session(Session)

def session_wrapper(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        session = SessionLocal()
        try:
            return func(self, session, *args, **kwargs)
        except jwt.InvalidTokenError as e:
            raise e
        except Exception as e:
            session.rollback()
            return HttpResp(Resp_code=500, resp_msg=str(e))
        finally:
            session.close()
        
    return wrapped

# 메일 전송
def send_email(email, title, content):
    gmail_smtp = 'smtp.gmail.com'
    gmail_port = 465
    smtp = smtplib.SMTP_SSL(gmail_smtp, gmail_port)
    sender_account = settings.EMAIL_ACCOUNT
    sender_password = settings.EMAIL_PASSWORD
    smtp.login(sender_account, sender_password)
    
    message = EmailMessage()
    message.set_content(content)
    
    message["Subject"] = title
    message["From"] = sender_account
    message["To"] = email

    smtp.send_message(message) 
    smtp.quit()

# 영문과 숫자 랜덤 조합
def generate_random_string(length):
    # 영문자와 숫자를 포함한 모든 문자를 사용합니다.
    characters = string.ascii_letters + string.digits
    # 지정된 길이 만큼 랜덤하게 문자열을 생성합니다.
    return ''.join(random.choice(characters) for _ in range(length))


# 닉네임 랜덤 생성
def generate_random_nick() -> str:
    a = ['눈부신', '따뜻한', '우수한', '은밀한', '침착한', 
    '잠든', '풍부한', '환상적인', '고요한', '느긋한', 
    '독특한', '위대한', '미묘한', '섬세한', '즐거운', 
    '행복한', '고독한', '신비로운', '찬란한', '조용한', 
    '빛나는', '화려한', '평화로운', '우아한', '뜨거운', 
    '차가운', '부드러운', '귀여운', '발랄한', '활발한']

    b = ['얼룩말', '양', '낙타', '사막여무', '기린', 
    '코끼리', '하마', '코알라', '나무늘보', '호랑이', 
    '사자', '부엉이', '고래', '상어', '개구리', 
    '구피', '고양이', '강아지', '햄스터', '카피바라', 
    '쿼카', '판다', '거북이', '토끼', '불가사리', 
    '해파리', '미어캣', '도마뱀', '기니피그', '사슴']
    
    nick = random.choice(a) + random.choice(b)
    return nick

RETURN_FUNC = lambda r: (r.resp_code, r)