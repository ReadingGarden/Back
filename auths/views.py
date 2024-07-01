import logging
import jwt

from ninja import Router, Schema
from pydantic import BaseModel, Field

from auths.authService import auth_service
from auths.permissions import UserAuth
from auths.tokenService import token_service
from cores.schema import DataResp, HttpResp, ServiceError
from cores.utils import RETURN_FUNC

logger = logging.getLogger("django.server")
router = Router(tags=["auth"])

class CreateUserSchema(Schema, BaseModel):
    user_email: str = Field("", alias="user_email", pattern=r"^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$")
    user_password: str = Field(..., alias="user_password")
    user_fcm: str = Field("", alias="user_fcm")
    user_social_id: str = Field("", alias="user_social_id")
    user_social_type: str = Field("", alias="user_social_type")

class LoginUserSchema(Schema, BaseModel):
   user_email: str = Field(..., alias="user_email")
   user_password: str = Field(..., alias="user_password")
   user_fcm: str = Field(..., alias="user_fcm")
   user_social_id: str = Field(..., alias="user_social_id")
   user_social_type: str = Field(..., alias="user_social_type")

class UserEmailSchema(Schema, BaseModel):
    user_email: str = Field(..., alias="user_email")

class UserPasswordAuthSchema(Schema, BaseModel):
    user_email: str = Field(..., alias="user_email")
    auth_number: str = Field(..., alias="auth_number")

class UpdateUserSchema(Schema, BaseModel):
    user_nick: str = Field("", alias="user_nick")
    user_image: str = Field("image1", alias="user_image")

class UpdateUserPasswordSchema(Schema, BaseModel):
    user_email: str = Field(None, alias="user_email")
    user_password: str = Field(..., alias="user_password")

class RefreshTokenSchema(Schema, BaseModel):
    refresh_token: str = Field(..., alias="refresh_token")
   

@router.post("/",
             response={201: DataResp, 409: HttpResp, 500: HttpResp}, 
             summary="유저 회원가입")
def create_user(request, form: CreateUserSchema):
    """
    회원가입
    """
    logger.info(f"user signup {form.dict(exclude={'user_password'})}")
    return RETURN_FUNC(auth_service.create_user(form.dict()))

@router.post(
   "/login",
   response={200: DataResp, 400: HttpResp, 500: HttpResp},
   summary="유저 로그인"
)
def login(request, form: LoginUserSchema):
   """
   로그인
   """
   logger.info(f"Call login API {form.dict(exclude={'user_password'})})")
   return RETURN_FUNC(auth_service.user_login(form.dict()))

@router.post(
   "/logout",
   auth=UserAuth(),
   response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
   summary="유저 로그아웃"
)
def logout(request):
   """
   로그아웃 (FCM 토큰 삭제)
   """
   logger.info(f"Call logout API")
   return RETURN_FUNC(auth_service.user_logout(request))

@router.post(
    "/refresh",
    response={200: DataResp, 401: HttpResp, 500: HttpResp},
    summary="유저 토큰 재발급"
)
def refresh(request, form: RefreshTokenSchema):
    """
    토큰 재발급
    """
    logger.info("Call refresh API")
    return RETURN_FUNC(token_service.refresh(form.dict()))

@router.delete(
   "/",
   auth=UserAuth(),
   response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
   summary="유저 회원 탈퇴"
)
def delete_user(request):
   """
   유저 회원 탈퇴
   """
   logger.info(f"Call delete_user API")
   return RETURN_FUNC(auth_service.user_delete(request))


@router.post(
    "/find-password",
    response={200: DataResp, 400: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="유저 비밀번호 인증 메일 전송"
)
def find_password(request, form: UserEmailSchema):
    """
    비밀번호 인증 메일 전송
    """
    return RETURN_FUNC(auth_service.user_find_password(form.dict()))


@router.post(
    "/find-password/check",
    response={200: DataResp, 400: HttpResp, 500: HttpResp},
    summary="유저 비밀번호 인증 확인"
)
def auth_check(request, form: UserPasswordAuthSchema):
    """
    비밀번호 인증 확인
    """
    return RETURN_FUNC(auth_service.user_auth_check(form.dict()))

@router.put(
    "/find-password/update-password",
    response={200: HttpResp, 400: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="유저 비밀번호 변경 (토큰 X)"
)
def update_password_no_token(request, form: UpdateUserPasswordSchema):
    """
    Update Password No Token
    """
    return RETURN_FUNC(auth_service.user_update_password_no_token(form.dict()))

@router.put(
    "/update-password",
    auth=UserAuth(),
    response={200: HttpResp, 400: HttpResp, 403: HttpResp, 500: HttpResp},
    summary="유저 비밀번호 변경 (토큰 O)"
)
def update_password(request, form: UpdateUserPasswordSchema):
    """
    Update Password With Token
    """
    return RETURN_FUNC(auth_service.user_update_password(request, form.dict()))

@router.get(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="유저 정보 조회"
)
def get_user(request):
    """
    프로필 조회
    """
    logger.info(f"Call get_user API")
    return RETURN_FUNC(auth_service.get_user(request))

@router.put(
    "/",
    auth=UserAuth(),
    response={200: DataResp, 400: HttpResp, 401: HttpResp, 500: HttpResp},
    summary="유저 프로필 수정"
)
def update_user(request, form: UpdateUserSchema):
    """
    프로필 수정
    """
    logger.info(f"Call update_user API")
    return RETURN_FUNC(auth_service.update_user(request, form.dict()))

