from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase
from cores.models import UtilModel

class MemoBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Memo(MemoBase, UtilModel):
    __tablename__ = "MEMO"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_no = Column(Integer, nullable=False)
    user_no = Column(Integer, nullable=False)
    memo_content = Column(Text, nullable=False)
    memo_quote = Column(Text, nullable=True)
    memo_like = Column(Boolean, nullable=False, default=False)    
    memo_created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

class MemoImage(MemoBase, UtilModel):
    __tablename__ = "MEMO_IMAGE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memo_no = Column(Integer, nullable=False)
    image_name = Column(Text, nullable=False)
    image_url = Column(Text, nullable=False)
    image_created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
