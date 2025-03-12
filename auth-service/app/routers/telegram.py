from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from ..database import get_db
from ..models.telegram import TelegramSession
from ..schemas.telegram import TelegramSessionCreate, TelegramSessionResponse
from supabase import Client
import logging
from datetime import datetime

router = APIRouter(
    prefix="",
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
        
        # Extract user_id and token from session_data if available
        user_id = session_data.session_data.get("user_id")
        token = session_data.session_data.get("auth_token")
        last_activity = session_data.session_data.get("last_activity", datetime.now().timestamp())
        
        if response.data and len(response.data) > 0:
            # Update existing session
            existing_session = response.data[0]
            updated_data = {
                "session_data": session_data.session_data,
                "last_activity": datetime.fromtimestamp(last_activity).isoformat()
            }
            
            # Add updated_at if the column exists in the table
            try:
                updated_data["updated_at"] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"Could not set updated_at: {str(e)}")
            
            # Update user_id and token if available
            if user_id:
                updated_data["user_id"] = user_id
            if token:
                updated_data["token"] = token
            
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
                "last_activity": datetime.fromtimestamp(last_activity).isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            # Add updated_at if the column exists in the table
            try:
                new_session_data["updated_at"] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"Could not set updated_at: {str(e)}")
            
            # Add user_id and token if available
            if user_id:
                new_session_data["user_id"] = user_id
            if token:
                new_session_data["token"] = token
            
            # If user_id is required but not available, use a default value
            if "user_id" not in new_session_data:
                # Get the default user ID (e.g., system user or guest user)
                default_user_response = supabase.table("users").select("id").eq("username", "system").execute()
                if default_user_response.data and len(default_user_response.data) > 0:
                    new_session_data["user_id"] = default_user_response.data[0]["id"]
                else:
                    # Create a temporary session with a placeholder user_id
                    # This is needed for unauthenticated users who are just starting to use the bot
                    logger.warning(f"No user_id available for telegram_id {session_data.telegram_id}, using placeholder")
                    
                    # Get any user as a placeholder (first user in the database)
                    any_user_response = supabase.table("users").select("id").limit(1).execute()
                    if any_user_response.data and len(any_user_response.data) > 0:
                        new_session_data["user_id"] = any_user_response.data[0]["id"]
                    else:
                        # If no users exist at all, we have a bigger problem
                        logger.error(f"No users found in the database, cannot create session")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="No users found in the database, cannot create session"
                        )
            
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
            # Return a 404 Not Found response instead of raising an exception
            # This allows the client to handle the case gracefully
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_data = response.data[0]
        
        # If session_data doesn't have the session_data field, create it
        if "session_data" not in session_data or not session_data["session_data"]:
            # Create session_data from the database fields
            session_data["session_data"] = {
                "telegram_id": session_data.get("telegram_id"),
                "user_id": session_data.get("user_id"),
                "auth_token": session_data.get("token"),
                "is_authenticated": session_data.get("token") is not None,
                "created_at": session_data.get("created_at"),
                "last_activity": session_data.get("last_activity")
            }
            
            # Update the session in the database
            supabase.table("telegram_sessions").update({
                "session_data": session_data["session_data"]
            }).eq("id", session_data["id"]).execute()
            
        return TelegramSession.from_dict(session_data)
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
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