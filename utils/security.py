import bcrypt

def hash_password(password: str) -> str:
    """
    Chuyển đổi mật khẩu (str) sang Hash (str) để lưu vào DB
    """
    # 1. Chuyển string sang bytes
    pwd_bytes = password.encode('utf-8')
    # 2. Tạo salt
    salt = bcrypt.gensalt()
    # 3. Hash (kết quả trả về là bytes)
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # 4. Decode ngược lại thành string để lưu vào MongoDB
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu nhập vào có khớp với Hash trong DB không
    """
    # 1. Chuyển cả 2 về dạng bytes
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # 2. Kiểm tra
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)