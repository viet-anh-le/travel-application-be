from jose import JWTError, jwt

SECRET_KEY = "xJF92kfja9#2LKafn29A$1ld8910F_zKF!2m"
ALGORITHM = "HS256"

def decode_access_token(token: str) -> dict | None:
    try:
        # Giải mã token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        print(f"JWTError: Could not validate credentials for token.")
        return None
    except Exception as e:
        print(f"An error occurred during token decoding: {e}")
        return None