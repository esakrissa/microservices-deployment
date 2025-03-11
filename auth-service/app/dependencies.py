from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from functools import lru_cache
from .config import Settings, get_settings
from .services.auth import AuthService
from .services.message_broker import MessageBroker
from .schemas.auth import TokenData, UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Create a single instance of the auth service
_auth_service = None

@lru_cache()
def get_message_broker(settings: Settings = Depends(get_settings)) -> MessageBroker:
    return MessageBroker(settings)

def get_auth_service(
    settings: Settings = Depends(get_settings),
    message_broker: MessageBroker = Depends(get_message_broker)
) -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(settings, message_broker)
    return _auth_service

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(username=email, permissions=payload.get("permissions", []))
    except JWTError:
        raise credentials_exception
        
    user = await auth_service.get_user_by_email(email=token_data.username)
    if user is None:
        raise credentials_exception
    return user 