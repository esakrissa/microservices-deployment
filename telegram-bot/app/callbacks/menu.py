import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle_menu_main_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the main menu callback."""
    return {
        "text": "🏠 *Main Menu*\n\nSelect an option:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🌍 Destinations", "callback_data": "menu_destinations"}],
                [{"text": "🎯 Activities", "callback_data": "menu_activities"}],
                [{"text": "📦 Packages", "callback_data": "menu_packages"}],
                [{"text": "👤 Account", "callback_data": "settings_account"}],
                [{"text": "⚙️ Settings", "callback_data": "settings_main"}]
            ]
        }
    }

async def handle_menu_destinations_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the destinations menu callback."""
    return {
        "text": "🌍 *Destinations*\n\nExplore popular travel destinations:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Europe", "callback_data": "destination_europe"}],
                [{"text": "Asia", "callback_data": "destination_asia"}],
                [{"text": "Americas", "callback_data": "destination_americas"}],
                [{"text": "Africa", "callback_data": "destination_africa"}],
                [{"text": "Oceania", "callback_data": "destination_oceania"}],
                [{"text": "🔙 Back to Main Menu", "callback_data": "menu_main"}]
            ]
        }
    }

async def handle_menu_activities_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the activities menu callback."""
    return {
        "text": "🎯 *Activities*\n\nDiscover exciting activities for your trip:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Adventure", "callback_data": "activity_adventure"}],
                [{"text": "Relaxation", "callback_data": "activity_relaxation"}],
                [{"text": "Cultural", "callback_data": "activity_cultural"}],
                [{"text": "Culinary", "callback_data": "activity_culinary"}],
                [{"text": "🔙 Back to Main Menu", "callback_data": "menu_main"}]
            ]
        }
    }

async def handle_menu_packages_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the packages menu callback."""
    return {
        "text": "📦 *Travel Packages*\n\nBrowse our curated travel packages:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Weekend Getaways", "callback_data": "package_weekend"}],
                [{"text": "Week-long Trips", "callback_data": "package_week"}],
                [{"text": "Extended Vacations", "callback_data": "package_extended"}],
                [{"text": "Special Offers", "callback_data": "package_special"}],
                [{"text": "🔙 Back to Main Menu", "callback_data": "menu_main"}]
            ]
        }
    } 