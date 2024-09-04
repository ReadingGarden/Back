from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase

from cores.models import UtilModel

class PushBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Push(PushBase, UtilModel):
    __tablename__ = "PUSH"

    user_no = Column(Integer, primary_key=True)
    push_app_ok = Column(Boolean, nullable=False)
    push_book_ok = Column(Boolean, nullable=False, default=False)
    push_time = Column(DateTime(timezone=True))
    
    
