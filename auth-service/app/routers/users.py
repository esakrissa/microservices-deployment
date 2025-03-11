from fastapi import APIRouter, Depends, HTTPException, status
from ..services.auth import AuthService
from ..schemas.auth import UserResponse, UserUpdate
from ..dependencies import get_auth_service, get_current_user
from typing import List

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    return current_user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    auth_service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return await auth_service.get_users()

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    try:
        updated_user = await auth_service.update_user(user_id, user_update)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 