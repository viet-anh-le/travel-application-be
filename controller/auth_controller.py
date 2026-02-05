from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import RedirectResponse
from services.auth_service import auth_service
from configs.google_calendar import oauth2_client
from models.auth_schema import (
    GoogleLoginRequest,
    SignUpRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResendOtpRequest,
    VerifyOtpRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
)
from middleware.auth_jwt import get_current_user_payload_strict

router = APIRouter(prefix="/auth", tags=["Auth"])

# =================================================================
# PROTECTED ROUTES (Cần đăng nhập - dùng get_current_user_payload_strict)
# =================================================================


@router.get("/me")
async def get_me(user_payload: dict = Depends(get_current_user_payload_strict)):
    return await auth_service.get_me(user_payload["id"])


@router.get("/google-calendar/authenticate")
async def google_calendar_authenticate(
    user_payload: dict = Depends(get_current_user_payload_strict),
):
    return await auth_service.google_calendar_authenticate(user_payload["id"])


@router.post("/refresh-token")
async def refresh_token(body: RefreshTokenRequest):
    return await auth_service.refresh_token(body.refresh_token)


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest, user_payload: dict = Depends(get_current_user_payload_strict)
):
    data = body.model_dump()
    data["user_id"] = user_payload["id"]

    return await auth_service.change_password(data)


# =================================================================
# PUBLIC ROUTES (Không cần đăng nhập)
# =================================================================


@router.get("/google-calendar/redirect")
async def google_calendar_redirect(request: Request):
    user_id = request.query_params.get("state")
    code = request.query_params.get("code")

    try:
        token_data = oauth2_client.fetch_token(code=code)
        await auth_service.google_calendar_save_token(user_id, token_data)

        return RedirectResponse(url="http://localhost:3000/plan")
    except Exception as e:
        print(f"Google Calendar Auth Error: {e}")
        return RedirectResponse(url="http://localhost:3000/error?msg=GoogleAuthFailed")


@router.post("/google-login")
async def google_login(body: GoogleLoginRequest):
    return await auth_service.google_login(body.token)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def sign_up(body: SignUpRequest):
    return await auth_service.sign_up(body.model_dump())


@router.post("/login")
async def login(body: LoginRequest):
    return await auth_service.login(body.model_dump())


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    return await auth_service.forgot_password(body.model_dump())


@router.post("/resend-otp")
async def resend_otp(body: ResendOtpRequest):
    return await auth_service.resend_otp(body.model_dump())


@router.post("/verify-otp")
async def verify_otp(body: VerifyOtpRequest):
    return await auth_service.verify_otp(body.model_dump())


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    return await auth_service.reset_password(body.model_dump())
