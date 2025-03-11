from .general import (
    handle_start_command,
    handle_help_command,
    handle_status_command,
    handle_menu_command,
    handle_settings_command
)

from .auth import (
    handle_register_command,
    handle_login_command,
    handle_register_email_state,
    handle_register_username_state,
    handle_register_password_state,
    handle_login_email_state,
    handle_login_password_state
)

# Create a mapping of commands to handlers
COMMAND_HANDLERS = {
    "/start": handle_start_command,
    "/help": handle_help_command,
    "/status": handle_status_command,
    "/menu": handle_menu_command,
    "/settings": handle_settings_command,
    "/register": handle_register_command,
    "/login": handle_login_command
}

# Create a mapping of states to handlers
STATE_HANDLERS = {
    "REGISTER_EMAIL": handle_register_email_state,
    "REGISTER_USERNAME": handle_register_username_state,
    "REGISTER_PASSWORD": handle_register_password_state,
    "LOGIN_EMAIL": handle_login_email_state,
    "LOGIN_PASSWORD": handle_login_password_state
}
