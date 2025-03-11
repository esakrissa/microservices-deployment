from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from ..database import get_db
from ..models.telegram import TelegramSession
from ..schemas.telegram import TelegramSessionCreate, TelegramSessionResponse
from supabase import Client
import logging
from datetime import datetime

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.post("/sessions", response_model=TelegramSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_session(
    session_data: TelegramSessionCreate,
    supabase: Client = Depends(get_db)
):
    """Create or update a Telegram session."""
    try:
        # Check if session already exists
        response = supabase.table("telegram_sessions").select("*").eq("telegram_id", session_data.telegram_id).execute()
        
        if response.data and len(response.data) > 0:
            # Update existing session
            existing_session = response.data[0]
            updated_data = {
                "session_data": session_data.session_data,
                "updated_at": datetime.now().isoformat()
            }
            
            update_response = supabase.table("telegram_sessions").update(updated_data).eq("id", existing_session["id"]).execute()
            
            if update_response.data and len(update_response.data) > 0:
                return TelegramSession.from_dict(update_response.data[0])
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update session"
                )
        else:
            # Create new session
            new_session_data = {
                "telegram_id": session_data.telegram_id,
                "session_data": session_data.session_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            insert_response = supabase.table("telegram_sessions").insert(new_session_data).execute()
            
            if insert_response.data and len(insert_response.data) > 0:
                return TelegramSession.from_dict(insert_response.data[0])
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create session"
                )
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

@router.get("/sessions/{telegram_id}", response_model=TelegramSessionResponse)
async def get_session(
    telegram_id: str,
    supabase: Client = Depends(get_db)
):
    """Get a Telegram session by telegram_id."""
    try:
        response = supabase.table("telegram_sessions").select("*").eq("telegram_id", telegram_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
        return TelegramSession.from_dict(response.data[0])
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

@router.delete("/sessions/{telegram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    telegram_id: str,
    supabase: Client = Depends(get_db)
):
    """Delete a Telegram session by telegram_id."""
    try:
        response = supabase.table("telegram_sessions").select("*").eq("telegram_id", telegram_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        delete_response = supabase.table("telegram_sessions").delete().eq("telegram_id", telegram_id).execute()
        
        return None
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        ) 