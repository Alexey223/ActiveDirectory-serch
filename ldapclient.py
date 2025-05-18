import os
import json
import getpass
from dotenv import load_dotenv
from logger_setup import log_info, log_error

# Load environment variables
load_dotenv()

current_user = getpass.getuser()

class LDAPClient:
    def __init__(self):
        self.ldap_user = os.getenv("LDAP_USER")
        self.ldap_password = os.getenv("LDAP_PASSWORD")
        self.connected = False # Initial state

        try:
            with open("sensitive_groups.json") as f:
                self.protected_groups = json.load(f).get("protected_groups", [])
        except FileNotFoundError:
            log_error("init", "sensitive_groups.json", "Sensitive groups file not found. No groups will be protected.")
            self.protected_groups = []
        except json.JSONDecodeError:
             log_error("init", "sensitive_groups.json", "Error decoding sensitive groups JSON. No groups will be protected.")
             self.protected_groups = []
        except Exception as e:
            log_error("init", "sensitive_groups.json", f"An unexpected error occurred loading sensitive groups: {e}. No groups will be protected.")
            self.protected_groups = []


    def connect(self, target: str = "localhost") -> bool:
        """Подключайся к указанному доменному контроллеру."""
        log_info("connect", target, f"Attempting to connect with user: {self.ldap_user}")
        print(f"[DEBUG] Попытка подключиться к [{target}]...")
        # Здесь будет подключаться к LDAP в будущем
        # For now, simulate connection success
        self.connected = True
        log_info("connect", target, "Connection established", status="success", user=current_user)
        return self.connected

    def is_connected(self) -> bool:
        return getattr(self, "connected", False)

    def add_user_to_group(self, user: str, group: str) -> bool:
        """Добавляет указанного пользователя в указанную группу."""
        log_info("addtogroup", group, f"Attempting to add user {user} to group {group}", user=current_user)

        if group in self.protected_groups:
            log_info("addtogroup", group, f"Group {group} is a protected group. Requesting confirmation.", user=current_user, status="pending_confirmation")
            print(f"⚠️ Warning: You are attempting to add {user} to a protected group: '{group}'. Confirm with [y/N]")
            confirmation = input().strip().lower()
            if confirmation != "y":
                log_info("addtogroup", group, "Operation cancelled by user", status="cancelled", user=current_user)
                print("Operation cancelled.")
                return False
            log_info("addtogroup", group, "User confirmed operation for protected group.", user=current_user)

        print(f"[DEBUG] Добавление [{user}] в [{group}]...")
        # Здесь будет реальное добавление
        # For now, simulate success
        log_info("addtogroup", group, f"Successfully added {user} to {group}", status="success", user=current_user)
        return True

    def get_status(self) -> str:
        """Возвращает текущее состояние подключения"""
        status = "✔ Подключено" if self.is_connected() else "❌ Нет подключения"
        log_info("status", "connection", f"Current status: {status}", user=current_user)
        return status 