from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase
from cores.models import UtilModel


class BookBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Book(BookBase, UtilModel):
    __tablename__ = "BOOK"

    book_no = Column(Integer, primary_key=True)
    book_isbn = Column(String(30), nullable=True)
    garden_no = Column(Integer, nullable=True)
    user_no = Column(Integer, nullable=False)
    book_title = Column(String(100), nullable=False)
    book_author = Column(String(100), nullable=False)
    book_publisher = Column(String(100), nullable=False)
    book_tree = Column(String(30), nullable=True)
    book_image_url = Column(Text, nullable=True)
    book_status = Column(Integer, nullable=False)
    book_page = Column(Integer, nullable=False)

class BookRead(BookBase, UtilModel):
    __tablename__ = "BOOK_READ"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_no = Column(Integer, nullable=False)
    user_no = Column(Integer, nullable=False)
    book_current_page = Column(Integer, nullable=False)
    book_start_date = Column(DateTime(timezone=True), nullable=True)
    book_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

class BookImage(BookBase, UtilModel):
    __tablename__ = "BOOK_IMAGE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_no = Column(Integer, nullable=False)
    image_name = Column(Text, nullable=False)
    image_url = Column(Text, nullable=False)
    image_created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)