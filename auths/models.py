from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase

from cores.models import UtilModel

class AuthBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class User(AuthBase, UtilModel):
    __tablename__ = "USER"

    user_no = Column(Integer, primary_key=True, autoincrement=True)
    user_nick = Column(String(30), nullable=False, default='')
    user_email = Column(String(300), nullable=False)
    user_password = Column(Text, nullable=False)
    user_fcm = Column(Text, nullable=False)
    user_social_id = Column(String(100), nullable=False, default='')
    user_social_type = Column(String(30), nullable=False, default='')
    user_image = Column(String(30), nullable=False, default='데이지')
    user_auth_number = Column(String(10), nullable=True)
    user_created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

class JWT(UtilModel):    
    abstract = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_no = Column(Integer, nullable=False)
    token = Column(Text)
    exp = Column(DateTime(timezone=True))

class RefreshToken(AuthBase, JWT):
    __tablename__ = "REFRESH_TOKEN"

    

