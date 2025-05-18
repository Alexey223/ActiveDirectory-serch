import os
import json
import getpass
from dotenv import load_dotenv
from logger_setup import log_info, log_error
# Import necessary ldap3 exceptions if handling them here
# from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError, LDAPException # Example if needed

# Load environment variables (only load once, perhaps at the app entry point)
# load_dotenv() # Moved to main.py entry point if needed for both CLI/GUI

# current_user = getpass.getuser() # Get user where action originates, e.g., in CLI/GUI handlers

class LDAPClient:
    # Add type hint for config argument
    def __init__(self, config: dict):
        # Load environment variables here if LDAPClient is the only place they are used, or pass them in.
        # Let's assume .env is loaded at the app entry point (e.g., in main.py's __main__ or a shared setup).
        # load_dotenv() # Load .env here if not loaded elsewhere

        self.config = config # Store the passed config
        self.ldap_user = os.getenv("LDAP_USER")
        self.ldap_password = os.getenv("LDAP_PASSWORD")
        self.connection = None # Use None for initial state
        self._connected = False # Internal state for connection status

        # Get AD settings from the passed config
        ad_settings = config.get('ad_settings', {})
        self.domain_controllers = ad_settings.get('domain_controllers', [])
        self.base_dn = ad_settings.get('base_dn', '')
        self.target_group_dn = ad_settings.get('target_group_dn', '')

        # Load protected groups
        try:
            with open("sensitive_groups.json") as f:
                self.protected_groups = json.load(f).get("protected_groups", [])
        except FileNotFoundError:
            # Use log_error from logger_setup
            log_error("init", "sensitive_groups.json", "Sensitive groups file not found. No groups will be protected.")
            self.protected_groups = []
        except json.JSONDecodeError:
             log_error("init", "sensitive_groups.json", "Error decoding sensitive groups JSON. No groups will be protected.")
             self.protected_groups = []
        except Exception as e:
            log_error("init", "sensitive_groups.json", f"An unexpected error occurred loading sensitive groups: {e}. No groups will be protected.")
            self.protected_groups = []

    # Update connect method signature to match usage in main.py
    # Add username and password parameters if LDAPClient should handle auth
    # Based on main.py usage, it seems username/password are passed via .env, so connect only needs target.
    # Let's revert connect signature back to only target for now based on CLI/GUI calls.
    def connect(self, target: str) -> tuple[bool, str]: # Reverted to target only
        """Подключайся к указанному доменному контроллеру."""
        # Get user who initiated the action (should be passed in or obtained at call site)
        # For logging in this method, assume user info is available or use a default
        action_user = getpass.getuser() # Or pass as argument

        # Log attempt with user from .env (ldap_user) and target
        log_info("connect", target, f"Attempting to connect with user: {self.ldap_user}", user=action_user)
        print(f"[DEBUG] Попытка подключиться к [{target}]...")

        # Placeholder for actual LDAP connection logic
        # try:
        #    server = Server(target, use_ssl=True, get_info=ALL)
        #    conn = Connection(server, user=self.ldap_user, password=self.ldap_password, client_strategy=SAFE_SYNC, auto_bind=True)
        #    if conn.bound:
        #        self.connection = conn
        #        self._connected = True
        #        log_info("connect", target, "Connection established", status="success", user=action_user)
        #        return True, f'Successfully connected to {target} as {self.ldap_user}'
        #    else:
        #        # Handle LDAP bind errors etc. based on conn.result
        #        error_desc = conn.result.get('description', 'Unknown error')
        #        error_diag = conn.result.get('diagnostic_message', 'N/A')
        #        log_error("connect", target, f"Connection failed: {error_desc} ({error_diag})", status="failure", user=action_user)
        #        self._connected = False
        #        return False, f'Connection failed: {error_desc} ({error_diag})'
        # except LDAPBindError as e:
        #    log_error("connect", target, f"Authentication failed: {str(e)}", status="failure", user=action_user)
        #    self._connected = False
        #    return False, f'Authentication failed: {str(e)}'
        # except LDAPSocketOpenError as e:
        #    log_error("connect", target, f"Server unreachable: {str(e)}", status="failure", user=action_user)
        #    self._connected = False
        #    return False, f'Server unreachable: {str(e)}'
        # except Exception as e:
        #    log_error("connect", target, f"Unexpected error during connect: {str(e)}", status="failure", user=action_user)
        #    self._connected = False
        #    return False, f'Unexpected error: {str(e)}'

        # Simulate connection success for prototype
        self._connected = True
        log_info("connect", target, "Connection established (simulated)", status="success", user=action_user)
        return True, "Successfully connected (simulated)"

    def is_connected(self) -> bool:
        # Use internal state variable
        return self._connected

    # Add user parameter to add_user_to_group for logging
    def add_user_to_group(self, user_dn: str, group_dn_or_name: str, user: str) -> tuple[bool, str]: # Added user parameter
        """Добавляет указанного пользователя в указанную группу."""
        # log attempt with user who initiated action and target group/user
        log_info("addtogroup", group_dn_or_name, f"Attempting to add user {user_dn} to group {group_dn_or_name}", user=user)

        # Check if group is protected using its name (assuming group_dn_or_name is the name for this check)
        # In a real app, you might need to resolve DN to name for this check, or store protected groups by DN
        if group_dn_or_name in self.protected_groups:
            log_info("addtogroup", group_dn_or_name, f"Group {group_dn_or_name} is a protected group. Requesting confirmation.", user=user, status="pending_confirmation")
            print(f"⚠️ Warning: You are attempting to add {user_dn} to a protected group: '{group_dn_or_name}'. Confirm with [y/N]")
            confirmation = input().strip().lower()
            if confirmation != "y":
                log_info("addtogroup", group_dn_or_name, "Operation cancelled by user", status="cancelled", user=user)
                print("Operation cancelled.")
                return False, "Operation cancelled by user"
            log_info("addtogroup", group_dn_or_name, "User confirmed operation for protected group.", user=user)

        # Placeholder for actual LDAP add logic
        # if not self.connection or not self.connection.bound:
        #    log_error("addtogroup", group_dn_or_name, "Not connected", status="failure", user=user)
        #    return False, "Not connected"
        # if not self.target_group_dn: # This assumes target_group_dn is always the group. Need to use group_dn_or_name instead.
        #    log_error("addtogroup", group_dn_or_name, "Target Group DN not configured", status="failure", user=user)
        #    return False, "Target Group DN not configured"
        # try:
        #    modification = [(self.connection.MODIFY_ADD, 'member', [user_dn])]
        #    # Use group_dn_or_name if it's the actual target DN for the modify operation
        #    self.connection.modify(group_dn_or_name, modification) # Assuming group_dn_or_name is the DN
        #    if self.connection.result.get('description') == 'success':
        #        log_info("addtogroup", group_dn_or_name, f"Successfully added user {user_dn}", status="success", user=user)
        #        return True, f'Successfully added user to group'
        #    else:
        #        error_desc = self.connection.result.get('description', 'Unknown error')
        #        error_diag = self.connection.result.get('diagnostic_message', 'N/A')
        #        log_error("addtogroup", group_dn_or_name, f"Add to group failed: {error_desc} ({error_diag})", status="failure", user=user)
        #        return False, f'Add to group failed: {error_desc} ({error_diag})'
        # except LDAPException as e:
        #    log_error("addtogroup", group_dn_or_name, f"LDAP error during add to group: {str(e)}", status="failure", user=user)
        #    return False, f'LDAP error during add to group: {str(e)}'
        # except Exception as e:
        #    log_error("addtogroup", group_dn_or_name, f"Unexpected error during add to group: {str(e)}", status="failure", user=user)
        #    return False, f'Unexpected error during add to group: {str(e)}'

        # Simulate success for prototype
        log_info("addtogroup", group_dn_or_name, f"Successfully added user {user_dn} (simulated)", status="success", user=user)
        return True, "Successfully added user to group (simulated)"

    def get_status(self) -> str: # This method is called by the user/system, so user context might be needed for logging here too.
        """Возвращает текущее состояние подключения"""
        # Get user who initiated the status check (should be passed in or obtained at call site)
        action_user = getpass.getuser() # Or pass as argument

        status = "✔ Подключено" if self.is_connected() else "❌ Нет подключения"
        # log_info("status", "connection", f"Current status: {status}", user=action_user) # get_status is diagnostic, maybe only print?
        # Removed logging from get_status as per previous plan, keep only print to stdout.
        return status

    # Add a method to get domain controllers for GUI to populate combobox
    def get_domain_controllers(self) -> list[str]:
        """Returns the list of domain controllers from the config."""
        return self.domain_controllers 