from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Optional, Dict, Any
from ..services.auth import AuthService
from ..schemas.auth import UserCreate, Token, UserResponse, TelegramLink
from ..dependencies import get_auth_service, get_current_user
import logging

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        user = await auth_service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        token = await auth_service.authenticate_user(form_data.username, form_data.password)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: Dict[str, Any],
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        email = credentials.get("email")
        password = credentials.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
            
        # Authenticate user
        token = await auth_service.authenticate_user(email, password)
        
        # If telegram_id is provided, link it to the user
        telegram_id = credentials.get("telegram_id")
        if telegram_id:
            try:
                # Get user by email
                user = await auth_service.get_user_by_email(email)
                if user:
                    # Link telegram account
                    await auth_service.link_telegram_account(user.id, telegram_id)
            except Exception as e:
                # Log error but don't fail the login
                logger.error(f"Error linking Telegram account: {str(e)}")
        
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/validate")
async def validate_token(
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token = authorization.replace("Bearer ", "")
        
        # Validate token
        payload = auth_service.validate_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {"valid": True, "user": payload}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating token",
        )

@router.post("/link-telegram", status_code=status.HTTP_200_OK)
async def link_telegram(
    telegram_data: TelegramLink,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        success = await auth_service.link_telegram_account(current_user.id, telegram_data.telegram_id)
        if success:
            return {"message": "Telegram account linked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to link Telegram account"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout a user and publish logout event."""
    try:
        success = await auth_service.logout_user(current_user.id)
        if success:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process logout"
            )
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        ) 