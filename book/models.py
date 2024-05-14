from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase
from cores.models import UtilModel


class BookBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Book(BookBase, UtilModel):
    __tablename__ = "BOOK"

    book_no = Column(String(30), primary_key=True)
    garden_no = Column(Integer, nullable=False)
    user_no = Column(Integer, nullable=False)
    book_title = Column(String(100), nullable=False)
    book_author = Column(String(100), nullable=False)
    book_publisher = Column(String(100), nullable=False)
    book_status = Column(Integer, nullable=False)
    book_page = Column(Integer, nullable=False)

class Book_Read(BookBase, UtilModel):
    __tablename__ = "BOOK_READ"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_no = Column(String(30), nullable=False)
    user_no = Column(Integer, nullable=False)
    book_current_page = Column(Integer, nullable=False)
    book_start_date = Column(DateTime(timezone=True), nullable=True)
    book_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

class Book_Memo(BookBase, UtilModel):
    __tablename__ = "BOOK_MEMO"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_no = Column(String(30), nullable=False)
    user_no = Column(Integer, nullable=False)
    memo_content = Column(Text, nullable=False)
    memo_like = Column(Boolean, nullable=False, default=False)    
    memo_created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
