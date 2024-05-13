from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase

from cores.models import UtilModel

class GardenBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"
    
class Garden(GardenBase, UtilModel):
    __tablename__ = "GARDEN"

    garden_no = Column(Integer, primary_key=True, autoincrement=True)
    garden_title = Column(String(30), nullable=False)
    garden_info = Column(String(200), nullable=False)
    garden_color = Column(String(20), nullable=False)
    garden_created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

class GardenUser(GardenBase, UtilModel):
    __tablename__ = "GARDEN_USER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    garden_no = Column(Integer, nullable=False)
    user_no = Column(Integer, nullable=False)
    garden_leader = Column(Boolean, nullable=False)
    garden_sign_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)


