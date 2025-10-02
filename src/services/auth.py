import os, datetime, jwt
from passlib.context import CryptContext

JWT_SECRET = os.environ.get("JWT_SECRET", "dev_secret_change_me")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "vo-console")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "vo-api")
JWT_EXPIRES_MIN = int(os.environ.get("JWT_EXPIRES_MIN", "120"))

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)

def make_token(sub: str, is_admin: bool=False) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": sub,
        "adm": is_admin,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=JWT_EXPIRES_MIN)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience=JWT_AUDIENCE, issuer=JWT_ISSUER)
