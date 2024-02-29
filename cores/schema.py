import logging
from typing import Generic, TypeVar

from pydantic import BaseModel, conint
from pydantic.generics import GenericModel

logger = logging.getLogger("django.server")
GenericResultsType = TypeVar("GenericResultsType")

class HttpResp(BaseModel):
    resp_code: conint(ge=0)
    resp_msg: str

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"{self.resp_code} {self.resp_msg}")


class DataResp(HttpResp, GenericModel, Generic[GenericResultsType]):
    data: GenericResultsType
    
class ServiceError(Exception):
    """
    Exception raised for errors in verifing token
    """
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(self.msg)

