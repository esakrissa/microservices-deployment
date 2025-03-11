from .menu import (
    handle_menu_main_callback,
    handle_menu_destinations_callback,
    handle_menu_activities_callback,
    handle_menu_packages_callback
)

from .settings import (
    handle_settings_main_callback,
    handle_settings_notifications_callback,
    handle_settings_preferences_callback,
    handle_settings_account_callback
)

from .auth import (
    handle_auth_register_callback,
    handle_auth_login_callback
)

# Create a mapping of callback data to handlers
CALLBACK_HANDLERS = {
    "menu_main": handle_menu_main_callback,
    "menu_destinations": handle_menu_destinations_callback,
    "menu_activities": handle_menu_activities_callback,
    "menu_packages": handle_menu_packages_callback,
    "settings_main": handle_settings_main_callback,
    "settings_notifications": handle_settings_notifications_callback,
    "settings_preferences": handle_settings_preferences_callback,
    "settings_account": handle_settings_account_callback,
    "auth_register": handle_auth_register_callback,
    "auth_login": handle_auth_login_callback
}
