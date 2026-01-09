from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from RAG.core.security import decode_access_token   

security = HTTPBearer(auto_error=False)

def get_user_payload_optional( authorization: HTTPAuthorizationCredentials | None = Depends(security)) -> dict | None:
    if authorization is None:
        # Không có header -> người dùng khách
        return None
        
    token = authorization.credentials    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token."
        )
    
    # payload sẽ là dict (nếu thành công) hoặc None (nếu thất bại)
    return payload

def get_current_user_payload_strict(
    user_payload: dict | None = Depends(get_user_payload_optional)
) -> dict:
    if user_payload is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. This feature is for logged-in users only."
        )
    return user_payload