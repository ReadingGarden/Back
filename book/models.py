from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from cores.models import UtilModel


class BookBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Book(BookBase, UtilModel):
    __tablename__ = "BOOK"

    book_no = Column(Integer, primary_key=True)
    garden_no = Column(Integer, nullable=False)
    book_title = Column(String(100), nullable=False)
    book_author = Column(String(100), nullable=False)
    book_publisher = Column(String(100), nullable=False)
    book_status = Column(Integer, nullable=False)
    book_current_page = Column(Integer, nullable=True)
    # book_start_date
    # book_end_date
