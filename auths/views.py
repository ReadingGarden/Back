import logging
import jwt

from ninja import Router, Schema
from pydantic import BaseModel, Field
from django.core.exceptions import ObjectDoesNotExist

from auths.authService import auth_service
from auths.permissions import UserAuth
from cores.schema import DataResp, HttpResp, ServiceError
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["auth_user"])

class UserSignUpSchema(Schema, BaseModel):
    user_email: str = Field("", alias="user_email", pattern=r"^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$")
    user_nick: str =Field(..., alias="user_nick")
    user_password: str = Field(..., alias="user_password")
    user_fcm: str = Field(..., alias="use_fcm")
    user_social_id: str = Field(..., alias="user_social_id")
    user_social_type: str = Field(..., alias="user_social_type")

class UserLoginSchema(Schema, BaseModel):
   user_email: str = Field(..., alias="user_email")
   user_password: str = Field(..., alias="user_password")
   user_fcm: str = Field(..., alias="use_fcm")
   user_social_id: str = Field(..., alias="user_social_id")
   user_social_type: str = Field(..., alias="user_social_type")

class UserEmailSchema(Schema, BaseModel):
    user_email: str = Field(..., alias="user_email")
   
@router.post("/signup",
             response={200: HttpResp, 409: HttpResp, 500: HttpResp}, 
             summary="유저 회원가입")
def signup(request, form: UserSignUpSchema):
    """
    Signup
    """
    logger.info(f"user signup {form.dict(exclude={'user_password'})}")
    return RETURN_FUNC(auth_service.user_signup(form.dict()))

@router.post(
   "/login",
   response={200: DataResp, 400: HttpResp, 500: HttpResp},
   summary="유저 로그인"
)
def login(request, form: UserLoginSchema):
   """
   Login
   """
   logger.info(f"Call login API {form.dict(exclude={'user_password'})})")
   return RETURN_FUNC(auth_service.user_login(form.dict()))

@router.get(
    "/user",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 500: HttpResp},
    summary="유저 정보 조회"
)
def get_user(request):
    """
    Get User
    """
    logger.info(f"Call user API")
    return RETURN_FUNC(auth_service.get_user(request))

@router.post(
    "/find_password",
    response={200: DataResp, 400: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="유저 비밀번호 인증 메일 전송"
)
def find_password(request, form: UserEmailSchema):
    """
    Find Password
    """
    return RETURN_FUNC(auth_service.user_find_password(form.dict()))
        


