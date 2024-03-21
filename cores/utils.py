from email.message import EmailMessage
from functools import wraps
import smtplib
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

RETURN_FUNC = lambda r: (r.resp_code, r)