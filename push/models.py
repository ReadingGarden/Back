from sqlalchemy import Boolean, Column, DateTime, Integer, inspect
from sqlalchemy.orm import DeclarativeBase

from cores.models import UtilModel

class PushBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Push(PushBase, UtilModel):
    __tablename__ = "PUSH"

    user_no = Column(Integer, primary_key=True)
    push_app_ok = Column(Boolean, nullable=False, default=False)
    push_book_ok = Column(Boolean, nullable=False, default=False)
    push_time = Column(DateTime(timezone=True))

    # 객체를 딕셔너리로 변환하는 메서드
    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
    
    
