import os
import httpx
import jwt
import datetime

from configs.google_calendar import oauth2_client, scopes
from configs.mailer import mail_template, send_google_success_email
from core.error_response import BadRequestError
from core.success_response import CreatedResponse, OkResponse
from models.user_schema import User
from utils.generate_code import generate_code
from constants.index import AUTH_PROVIDER, ROLE
from RAG.config.redis_cache import redis_client
from utils.security import hash_password, verify_password

# --- Cấu hình giả lập & Helper ---
SECRET_KEY = os.getenv("DEV_JWT_SECRET_KEY", "xJF92kfja9#2LKafn29A$1ld8910F_zKF!2m")

#-------Cấu hình thời gian hết hạn: int(ms), s/m/h/d-----
def get_expiration_delta(expiration: str | int) -> datetime.timedelta:
    if isinstance(expiration, int):
        return datetime.timedelta(milliseconds=expiration)
    
    unit = expiration[-1]
    value = int(expiration[:-1])
    if unit == 'd': return datetime.timedelta(days=value)
    if unit == 'h': return datetime.timedelta(hours=value)
    if unit == 'm': return datetime.timedelta(minutes=value)
    if unit == 's': return datetime.timedelta(seconds=value)
    return datetime.timedelta(days=1)

def generate_jwt(payload: dict, expiration="1d") -> str:
    delta = get_expiration_delta(expiration)
    expire = datetime.datetime.now() + delta
    to_encode = payload.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

class AuthService:
    async def get_me(self, user_id: str):
        user = await User.get(user_id)
        if not user:
            raise BadRequestError("Không tìm thấy người dùng")
        
        return OkResponse("Lấy thông tin người dùng thành công", user.model_dump(exclude={"password"}))

    async def google_login(self, token: str):
        if not token:
            raise BadRequestError("Token truy cập Google là bắt buộc")
        
        email, name, picture, sub = None, None, None, None

        try:
            async with httpx.AsyncClient() as client:
                google_response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                payload = google_response.json()
                
                email = payload.get("email")
                name = payload.get("name")
                picture = payload.get("picture")
                sub = payload.get("sub")
        except Exception:
             raise BadRequestError("Token truy cập Google không hợp lệ")

        if not email:
            raise BadRequestError("Tài khoản Google không có email hợp lệ")

        found_user = await User.find_one({
            "$or": [{"email": email}, {"google_id": sub}]
        })

        if not found_user:
            new_user = User(
                full_name=name or "Traveler",
                email=email,
                address="",
                avatar=picture or "",
                role=ROLE.USER,
                auth_provider=AUTH_PROVIDER.GOOGLE,
                google_id=sub
            )
            await new_user.create()
            found_user = new_user

            # Mock gửi email
            await send_google_success_email({
                "to": email,
                "name": name or "Traveler",
                "login_link": "http://localhost:3000/signin"
            })

        if found_user.avatar == "" and picture:
            found_user.avatar = picture
            await found_user.save()

        token_payload = {
            "email": found_user.email,
            "id": str(found_user.id),
            "full_name": found_user.full_name,
            "role": found_user.role,
        }

        access_token = generate_jwt(token_payload, "2h")
        refresh_token = generate_jwt(token_payload, "7d")

        user_data = found_user.model_dump(exclude={"password"})
        user_data["id"] = str(found_user.id)
        
        return OkResponse("Login successfully", {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data
        })

    async def sign_up(self, payload: dict):
        existing_user = await User.find_one({"email": payload['email']})
        if existing_user:
            raise BadRequestError("Email đã được đăng ký")
        
        username = payload['email'].split("@")[0]
        
        hashed_password = hash_password(payload['password'])
        
        new_user = User(
            full_name=payload['full_name'],
            email=payload['email'],
            password=hashed_password,
            username=username
        )
        await new_user.create()
        
        if not new_user:
             raise BadRequestError("Tạo người dùng thất bại")

        await send_google_success_email({
            "to": payload['email'],
            "name": payload['full_name'] or "Traveler",
            "login_link": "http://localhost:3000/signin",
        })

        user_data = new_user.model_dump(exclude={"password"})
        return CreatedResponse("Create user successfully", user_data)

    async def login(self, payload: dict):
        user = await User.find_one({"email": payload['email']})
        if not user:
            raise BadRequestError("Email chưa được đăng ký")

        is_password_valid = verify_password(payload['password'], user.password)
        if not is_password_valid:
             raise BadRequestError("Mật khẩu không chính xác")

        token_payload = {
            "email": user.email,
            "id": str(user.id),
            "full_name": user.full_name,
            "role": user.role,
        }

        access_token = generate_jwt(token_payload, "2h")
        refresh_token = generate_jwt(token_payload, "7d")

        user_data = user.dict(exclude={"password"})
        user_data['id'] = str(user.id)
        return OkResponse("Login successfully", {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data
        })

    async def refresh_token(self, payload: dict):
        user = await User.get(payload['id'])
        if not user:
            raise BadRequestError("Không tìm thấy người dùng")

        token_payload = {
            "email": user.email,
            "id": str(user.id),
            "full_name": user.full_name,
            "role": user.role,
        }

        access_token = generate_jwt(token_payload, "2h")
        refresh_token = generate_jwt(token_payload, "7d")

        return OkResponse("Token refreshed successfully", {
            "access_token": access_token,
            "refresh_token": refresh_token,
        })

    async def forgot_password(self, payload: dict):
        user = await User.find_one({"email": payload['email']})
        if not user:
            raise BadRequestError("Email is not found in system")

        expire_in = 120 # seconds
        code = generate_code(6)
        
        hash_otp = hash_password(code)
        
        # Lưu vào Redis
        await redis_client.set(f"OTP-{user.id}", hash_otp, ex=expire_in)

        await mail_template({
            "code": code,
            "from_email": "Nomado Support",
            "to": payload['email'],
            "subject": "Đặt lại mật khẩu của bạn",
            "text": f"""<p>Vui lòng sử dụng mã OTP dưới đây để đặt lại mật khẩu của bạn:</p>
                <a href="http://example.com/reset-password?email={payload['email']}">Thay đổi mật khẩu</a>"""
        })
        
        return OkResponse("OTP sent to your email", {
            "user_id": str(user.id),
            "expireIn": expire_in
        })

    async def resend_otp(self, payload: dict):
        user = await User.get(payload['user_id'])
        if not user:
            raise BadRequestError("Không tìm thấy người dùng")

        existing_otp = await redis_client.get(f"OTP-{user.id}")
        if existing_otp:
            raise BadRequestError("OTP vẫn còn hiệu lực. Vui lòng kiểm tra email của bạn")

        expire_in = 120
        code = generate_code(6)
        hash_otp = hash_password(code)
        
        await redis_client.set(f"OTP-{user.id}", hash_otp, ex=expire_in)

        await mail_template({
            "code": code,
            "from_email": "Nomado Support",
            "to": user.email,
            "subject": "Gửi lại OTP để đặt lại mật khẩu",
            "text": f"""<p>Vui lòng sử dụng mã OTP dưới đây để đặt lại mật khẩu của bạn:</p>
                <a href="http://example.com/reset-password?email={user.email}">Thay đổi mật khẩu</a>"""
        })

        return OkResponse("OTP resent to your email", {
            "user_id": str(user.id),
            "expireIn": expire_in
        })

    async def verify_otp(self, payload: dict):
        user = await User.get(payload['user_id'])
        if not user:
            raise BadRequestError("Không tìm thấy người dùng")

        stored_otp_hash = await redis_client.get(f"OTP-{user.id}")
        if not stored_otp_hash:
            raise BadRequestError("OTP đã hết hạn hoặc không hợp lệ")

        is_otp_valid = verify_password(payload['otp'], stored_otp_hash)
        if not is_otp_valid:
            raise BadRequestError("OTP không hợp lệ")

        reset_token = jwt.encode(
            {"user_id": str(payload['user_id']), "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)},
            SECRET_KEY,
            algorithm="HS256"
        )
        
        await redis_client.delete(f"OTP-{user.id}")

        return OkResponse("OTP verified successfully", {"reset_token": reset_token})

    async def reset_password(self, payload: dict):
        try:
            decode_token = jwt.decode(payload['reset_token'], SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
             raise BadRequestError("Token đã hết hạn")
        except jwt.InvalidTokenError:
             raise BadRequestError("Token không hợp lệ")

        user_id = decode_token.get("user_id")
        found_user = await User.get(user_id)

        if not found_user:
            raise BadRequestError("Không tìm thấy người dùng")

        is_existing_password =  verify_password(payload['password'], found_user.password)
        if is_existing_password:
            raise BadRequestError("Mật khẩu mới phải khác mật khẩu cũ")

        found_user.password = hash_password(payload['password'])
        await found_user.save()

        return OkResponse("Password reset successfully")

    async def google_calendar_save_token(self, user_id: str, tokens: dict):
        user = await User.get(user_id)
        if not user:
             raise BadRequestError("User not found")

        print(f"======Tokens = {tokens}==============")
        user.google_calendar = {
            "email": user.email,
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "scope": tokens.get("scope"),
            "token_type": tokens.get("token_type"),
            "expiry_date": tokens.get("expires_at"),
        }
        await user.save()

        return OkResponse("Google Calendar tokens saved successfully", {"user_id": user_id})

    async def change_password(self, payload: dict):
        old_password = payload['old_password']
        new_password = payload['new_password']
        user_id = payload['user_id']

        user = await User.get(user_id)
        if not user:
            raise BadRequestError("User not found")

        is_old_password_valid = verify_password(old_password, user.password)
        if not is_old_password_valid:
            raise BadRequestError("Mật khẩu cũ không đúng")

        is_same_password = verify_password(new_password, user.password)
        if is_same_password:
            raise BadRequestError("Mật khẩu mới phải khác mật khẩu cũ")

        user.password = hash_password(new_password)
        await user.save()

        return OkResponse("Password changed successfully")

    async def google_calendar_authenticate(self, user_id: str):
        found_user = await User.get(user_id)
        if not found_user:
            raise BadRequestError("User not found")
        
        if (found_user.google_calendar and 
            found_user.google_calendar.access_token and 
            found_user.google_calendar.expiry_date):
            
            now = datetime.datetime.utcnow().timestamp()
            if found_user.google_calendar.expiry_date > now:
                return OkResponse("Google Calendar is already authenticated")
            
        url, _ = oauth2_client.authorization_url(
            access_type='offline',  
            state=user_id,          
            prompt='consent',       
            include_granted_scopes='true' ,
        )    
        print(f"Generated Auth URL: {url}")
        return OkResponse("Google Calendar authentication URL", {"url": url})
auth_service = AuthService()