import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle_settings_main_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the settings menu callback."""
    return {
        "text": "⚙️ *Settings*\n\nSelect an option:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🔔 Notifications", "callback_data": "settings_notifications"}],
                [{"text": "⭐ Preferences", "callback_data": "settings_preferences"}],
                [{"text": "👤 Account", "callback_data": "settings_account"}],
                [{"text": "🏠 Back to Main Menu", "callback_data": "menu_main"}]
            ]
        }
    }

async def handle_settings_notifications_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the notifications settings callback."""
    return {
        "text": "🔔 *Notification Settings*\n\nManage your notification preferences:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Deals & Promotions", "callback_data": "toggle_deals_notifications"}],
                [{"text": "Travel Updates", "callback_data": "toggle_travel_notifications"}],
                [{"text": "Account Activity", "callback_data": "toggle_account_notifications"}],
                [{"text": "⬅️ Back to Settings", "callback_data": "settings_main"}]
            ]
        }
    }

async def handle_settings_preferences_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the preferences settings callback."""
    return {
        "text": "⭐ *Preferences*\n\nCustomize your travel preferences:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Preferred Destinations", "callback_data": "pref_destinations"}],
                [{"text": "Travel Style", "callback_data": "pref_travel_style"}],
                [{"text": "Budget Range", "callback_data": "pref_budget"}],
                [{"text": "⬅️ Back to Settings", "callback_data": "settings_main"}]
            ]
        }
    }

async def handle_settings_account_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the account settings callback."""
    return {
        "text": "👤 *Account Settings*\n\nManage your account:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🔑 Login", "callback_data": "auth_login"}],
                [{"text": "📝 Register", "callback_data": "auth_register"}],
                [{"text": "📋 Profile", "callback_data": "account_profile"}],
                [{"text": "🔄 Change Password", "callback_data": "account_change_password"}],
                [{"text": "⬅️ Back to Settings", "callback_data": "settings_main"}]
            ]
        }
    } 