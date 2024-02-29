from sqlalchemy.orm import DeclarativeBase

class UtilModel:
    __table__ = None
    
    def as_dict(self, exclude: list = []):
        data = {}

        # 현재 클래스와 상속받은 클래스(mro)에서 테이블이 정의된 경우
        for cls in [self.__class__] + self.__class__.mro():
            if hasattr(cls, "__table__") and cls.__table__ is not None:
                # 테이블의 각 컬럼을 반복하면서 딕셔너리에 추가 (exclude에 포함되지 않는 경우)
                data.update(
                    {
                        c.name: getattr(self, c.name)
                        for c in cls.__table__.columns
                        if c.name not in exclude
                    }
                )
        return data
    
class UtilBase(DeclarativeBase):
    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}"
