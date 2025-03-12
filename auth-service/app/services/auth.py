from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from supabase import create_client, Client
from ..config import Settings
from ..schemas.auth import UserCreate, UserResponse, Token, UserUpdate
from .message_broker import MessageBroker
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, settings: Settings, message_broker: Optional[MessageBroker] = None):
        self.settings = settings
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.message_broker = message_broker
        
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        response = self.supabase.table('users').select('*').eq('email', email).execute()
        if len(response.data) == 0:
            return None
        return UserResponse(**response.data[0])

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        # Check if user exists
        if await self.get_user_by_email(user_data.email):
            raise ValueError("Email already registered")
            
        # Hash password
        hashed_password = pwd_context.hash(user_data.password)
        
        # Create user in Supabase
        user_dict = user_data.model_dump()
        
        # Extract telegram data if present
        telegram_id = user_dict.pop("telegram_id", None)
        telegram_username = user_dict.pop("telegram_username", None)
        
        # Remove password and add password_hash
        del user_dict["password"]
        user_dict["password_hash"] = hashed_password
        user_dict["is_active"] = True
        user_dict["permissions"] = self._get_role_permissions(user_data.role)
        
        # Create user
        response = self.supabase.table('users').insert(user_dict).execute()
        user = UserResponse(**response.data[0])
        
        # Link telegram account if telegram_id is provided
        if telegram_id:
            try:
                telegram_data = {
                    "user_id": user.id,
                    "telegram_id": telegram_id,
                    "username": telegram_username or user.username
                }
                self.supabase.table('telegram_accounts').insert(telegram_data).execute()
                logger.info(f"Linked Telegram account {telegram_id} to user {user.id}")
            except Exception as e:
                logger.error(f"Error linking Telegram account: {str(e)}")
        
        # Publish user registered event
        if self.message_broker:
            await self.message_broker.publish_message(
                topic="auth.user.registered",
                message={
                    "event": "user_registered",
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        return user

    async def authenticate_user(self, email: str, password: str) -> Token:
        user = await self.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")
            
        response = self.supabase.table('users').select('password_hash').eq('email', email).execute()
        if not pwd_context.verify(password, response.data[0]['password_hash']):
            raise ValueError("Invalid credentials")
            
        # Create access token
        access_token = self._create_access_token(
            data={"sub": user.email, "permissions": user.permissions}
        )
        
        # Publish user login event
        if self.message_broker:
            await self.message_broker.publish_message(
                topic="auth.user.login",
                message={
                    "event": "user_login",
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        return Token(access_token=access_token)

    async def get_users(self) -> list[UserResponse]:
        response = self.supabase.table('users').select('*').execute()
        return [UserResponse(**user) for user in response.data]

    async def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = pwd_context.hash(update_data["password"])
        if "role" in update_data:
            update_data["permissions"] = self._get_role_permissions(update_data["role"])
            
        response = self.supabase.table('users').update(update_data).eq('id', user_id).execute()
        if len(response.data) == 0:
            raise ValueError("User not found")
            
        user = UserResponse(**response.data[0])
        
        # Publish user updated event
        if self.message_broker:
            await self.message_broker.publish_message(
                topic="auth.user.updated",
                message={
                    "event": "user_updated",
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        return user
        
    async def link_telegram_account(self, user_id: str, telegram_id: str) -> bool:
        """Link a Telegram account to a user."""
        try:
            # Check if telegram account already exists
            response = self.supabase.table('telegram_accounts').select('*').eq('telegram_id', telegram_id).execute()
            
            if len(response.data) > 0:
                # Update existing telegram account
                telegram_account = response.data[0]
                if telegram_account['user_id'] != user_id:
                    self.supabase.table('telegram_accounts').update({'user_id': user_id}).eq('id', telegram_account['id']).execute()
                    logger.info(f"Updated Telegram account {telegram_id} to user {user_id}")
            else:
                # Create new telegram account
                user_response = self.supabase.table('users').select('username').eq('id', user_id).execute()
                if len(user_response.data) == 0:
                    raise ValueError("User not found")
                    
                username = user_response.data[0]['username']
                telegram_data = {
                    "user_id": user_id,
                    "telegram_id": telegram_id,
                    "username": username
                }
                self.supabase.table('telegram_accounts').insert(telegram_data).execute()
                logger.info(f"Linked Telegram account {telegram_id} to user {user_id}")
                
            # Publish telegram account linked event
            if self.message_broker:
                await self.message_broker.publish_message(
                    topic="auth.telegram.linked",
                    message={
                        "event": "telegram_linked",
                        "user_id": user_id,
                        "telegram_id": telegram_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
            return True
        except Exception as e:
            logger.error(f"Error linking Telegram account: {str(e)}")
            return False
            
    async def logout_user(self, user_id: str) -> bool:
        """Log out a user and publish logout event."""
        try:
            # Get user information for the event
            user_response = self.supabase.table('users').select('email,username').eq('id', user_id).execute()
            if len(user_response.data) == 0:
                logger.warning(f"User {user_id} not found for logout event")
                return False
                
            user_data = user_response.data[0]
            
            # Publish user logout event
            if self.message_broker:
                await self.message_broker.publish_message(
                    topic="auth.user.logout",
                    message={
                        "event": "user_logout",
                        "user_id": user_id,
                        "username": user_data.get('username'),
                        "email": user_data.get('email'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"Published logout event for user {user_id}")
                
            return True
        except Exception as e:
            logger.error(f"Error publishing logout event: {str(e)}")
            return False

    def _create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM
        )

    def _get_role_permissions(self, role: str) -> list[str]:
        # Define role-based permissions
        permissions_map = {
            "admin": ["read:users", "write:users", "delete:users", "manage:roles"],
            "moderator": ["read:users", "write:users"],
            "user": ["read:own_profile"]
        }
        return permissions_map.get(role, ["read:own_profile"])

    def validate_token(self, token: str) -> Optional[dict]:
        """Validate a JWT token and return the payload if valid."""
        try:
            payload = jwt.decode(
                token, 
                self.settings.JWT_SECRET_KEY, 
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None 

    async def get_telegram_id_for_user(self, user_id: str) -> Optional[str]:
        """Get the Telegram ID for a user."""
        try:
            response = self.supabase.table('telegram_accounts').select('telegram_id').eq('user_id', user_id).execute()
            if len(response.data) == 0:
                return None
            return response.data[0]['telegram_id']
        except Exception as e:
            logger.error(f"Error getting Telegram ID for user {user_id}: {str(e)}")
            return None 