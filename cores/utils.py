from functools import wraps
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

RETURN_FUNC = lambda r: (r.resp_code, r)