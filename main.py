import sys
import logging
import json
import os
import argparse
from enum import Enum
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QComboBox, QLineEdit, QVBoxLayout, QWidget, QListWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QByteArray, QEasingCurve
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from ldap3 import Server, Connection, SAFE_SYNC, SUBTREE, ALL
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError, LDAPException

# Import LDAPClient and logging setup
from ldapclient import LDAPClient
from logger_setup import log_info, log_error, log_warning

# Constants
DEFAULT_CONFIG_PATH = 'config.json'
DEFAULT_WINDOW_SIZE = (600, 650)
DEFAULT_WINDOW_POSITION = (100, 100)

# UI Constants
ICON_SIZE = QSize(20, 20)
BUTTON_MIN_WIDTH = 120
BUTTON_PADDING = (10, 20)
LIST_ITEM_PADDING = (8, 5)

# Color Constants
COLORS = {
    'background': '#121212',
    'surface': '#1E1E1E',
    'primary': '#E0E0E0',
    'accent': '#81D8D0',
    'accent_hover': '#A0E0D8',
    'accent_pressed': '#61B8B0',
    'border': '#A0A0A0',
    'success': '#81C784',
    'error': '#E57373',
    'disabled': '#A0A0A0'
}

# Status Messages
class StatusMessage:
    NOT_CONNECTED = 'Status: Not connected'
    CONNECTED = 'Status: Connected to {} as {}'
    DISCONNECTED = 'Status: Disconnected'
    CONNECTION_ERROR = 'Status: Connection error'
    AUTH_FAILED = 'Status: Authentication failed'
    SERVER_UNREACHABLE = 'Status: Server unreachable'
    CONNECTION_FAILED = 'Status: Connection failed'
    ADD_SUCCESS = 'Status: Added {} to group (success)'
    ADD_FAILED = 'Status: Add to group failed'

# LDAP Search Attributes
LDAP_ATTRIBUTES = ['sAMAccountName', 'cn', 'distinguishedName']

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(), # Output to console
        # FileHandler is added after reading config
    ]
)

logger = logging.getLogger(__name__)

def load_config(config_path=DEFAULT_CONFIG_PATH):
    """Loads configuration from a JSON file."""
    config = {}
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        QMessageBox.critical(None, "Configuration Error", f"Configuration file not found: {config_path}")
        return None
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}.")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {config_path}: {e}")
        QMessageBox.critical(None, "Configuration Error", f"Error decoding JSON from {config_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred while reading {config_path}: {e}")
        QMessageBox.critical(None, "Configuration Error", f"An error occurred while reading {config_path}: {e}")
        return None

def load_svg_icon(filepath, color=None, size=None):
    """Loads an SVG file, optionally recolors and resizes it, and returns a QIcon."""
    renderer = QSvgRenderer(filepath)
    if not renderer.isValid():
        logger.warning(f"Failed to load SVG file: {filepath}")
        return QIcon() # Return empty icon on failure

    if size is None:
        # Use the SVG's intrinsic size if no size is specified
        size = renderer.defaultSize()

    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    if color is not None:
        # Recolor the SVG by painting it through a color overlay
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(0, 0, size.width(), size.height(), QColor(color))
    else:
        # Render without recoloring
        renderer.render(painter)
    painter.end()

    return QIcon(pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = load_config(DEFAULT_CONFIG_PATH)
        if not self.config:
            sys.exit(1)
            
        # Initialize LDAP client
        self.ldap_client = LDAPClient(self.config)
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize and setup the user interface."""
        self.setWindowTitle('Active Directory Utility')
        self.setGeometry(*DEFAULT_WINDOW_POSITION, *DEFAULT_WINDOW_SIZE)
        
        # Apply stylesheet
        self._apply_stylesheet()
        
        # Create central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Setup UI components
        self._setup_domain_controller(layout)
        self._setup_credentials(layout)
        self._setup_connect_button(layout)
        self._setup_status_label(layout)
        self._setup_search_section(layout)
        
        # Initial state
        self._update_ui_state(False)
        
    def _apply_stylesheet(self):
        """Apply the application stylesheet."""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
                color: {COLORS['primary']};
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: 14px;
            }}
            
            QWidget {{
                padding: 15px;
            }}
            
            QLabel {{
                color: {COLORS['primary']};
                font-size: 14px;
                margin-bottom: 4px;
                font-weight: 500;
            }}
            
            QLineEdit, QComboBox, QListWidget {{
                background-color: {COLORS['surface']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px;
                selection-background-color: {COLORS['accent']};
                selection-color: {COLORS['background']};
                margin-bottom: 10px;
                outline: none;
            }}
            
            QLineEdit:focus, QComboBox:focus, QListWidget:focus {{
                border-color: {COLORS['accent']};
            }}
            
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['background']};
                border: none;
                border-radius: 5px;
                padding: {BUTTON_PADDING[0]}px {BUTTON_PADDING[1]}px;
                min-width: {BUTTON_MIN_WIDTH}px;
                margin-top: 5px;
                margin-bottom: 10px;
                font-weight: bold;
                text-align: left;
                padding-left: 15px;
            }}
            
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
                color: {COLORS['surface']};
            }}
            
            QPushButton:pressed {{
                background-color: {COLORS['accent_pressed']};
            }}
            
            QPushButton:disabled {{
                background-color: {COLORS['surface']};
                color: {COLORS['disabled']};
                border: none;
            }}
            
            QListWidget {{
                margin-top: 8px;
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
            }}
            
            QListWidget::item {{
                padding: {LIST_ITEM_PADDING[0]}px {LIST_ITEM_PADDING[1]}px;
                border-bottom: 1px solid {COLORS['surface']};
            }}
            
            QListWidget::item:last {{
                border-bottom: none;
            }}
            
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: {COLORS['surface']};
            }}
            
            QLabel#status_label {{
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 5px;
                font-size: 13px;
            }}
        """)
    
    def _setup_domain_controller(self, layout):
        """Setup domain controller selection."""
        domain_layout = QVBoxLayout()
        self.domain_label = QLabel('Domain Controller:')
        domain_layout.addWidget(self.domain_label)
        
        domain_controllers = self.ldap_client.get_domain_controllers()
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(domain_controllers)
        self.domain_combo.currentIndexChanged.connect(self.on_domain_changed)
        domain_layout.addWidget(self.domain_combo)
        
        layout.addLayout(domain_layout)
    
    def _setup_credentials(self, layout):
        """Setup username and password fields."""
        creds_layout = QVBoxLayout()
        
        self.username_label = QLabel('Username:')
        creds_layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        creds_layout.addWidget(self.username_input)
        
        self.password_label = QLabel('Password:')
        creds_layout.addWidget(self.password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        creds_layout.addWidget(self.password_input)
        
        layout.addLayout(creds_layout)
    
    def _setup_connect_button(self, layout):
        """Setup connect/disconnect button."""
        self.connect_btn = QPushButton('Connect')
        try:
            connect_icon = load_svg_icon('icons/connect_icon.svg', 
                                       color=COLORS['primary'], 
                                       size=ICON_SIZE)
            self.connect_btn.setIcon(connect_icon)
        except Exception as e:
            logger.warning(f"Could not load connect icon: {e}")
        
        self.connect_btn.clicked.connect(self.on_connect)
        layout.addWidget(self.connect_btn)
    
    def _setup_status_label(self, layout):
        """Setup status label."""
        self.status_label = QLabel(StatusMessage.NOT_CONNECTED)
        self.status_label.setObjectName('status_label')
        self.status_label.setStyleSheet(f'color: {COLORS["disabled"]}')
        layout.addWidget(self.status_label)
        
        layout.addSpacing(20)
    
    def _setup_search_section(self, layout):
        """Setup search section with results list and add button."""
        search_layout = QVBoxLayout()
        
        # Search input
        self.search_label = QLabel('Search User:')
        search_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        
        # Search button
        self.search_btn = QPushButton('Search')
        try:
            search_icon = load_svg_icon('icons/search_icon.svg', 
                                      color=COLORS['primary'], 
                                      size=ICON_SIZE)
            self.search_btn.setIcon(search_icon)
        except Exception as e:
            logger.warning(f"Could not load search icon: {e}")
        
        self.search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_btn)
        
        # Results section
        results_layout = QHBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.on_result_selected)
        results_layout.addWidget(self.results_list)
        
        # Add to group button
        target_group_dn = self.config.get('ad_settings', {}).get('target_group_dn', '')
        self.add_group_btn = QPushButton(f'Add to {target_group_dn}')
        try:
            add_icon = load_svg_icon('icons/add_icon.svg', 
                                   color=COLORS['background'], 
                                   size=ICON_SIZE)
            self.add_group_btn.setIcon(add_icon)
        except Exception as e:
            logger.warning(f"Could not load add icon: {e}")
        
        self.add_group_btn.clicked.connect(self.on_add_to_group)
        results_layout.addWidget(self.add_group_btn)
        
        results_layout.setStretchFactor(self.results_list, 3)
        results_layout.setStretchFactor(self.add_group_btn, 1)
        
        search_layout.addLayout(results_layout)
        layout.addLayout(search_layout)
    
    def _update_ui_state(self, connected: bool):
        """Update UI elements based on connection state."""
        self.search_label.setEnabled(connected)
        self.search_input.setEnabled(connected)
        self.search_btn.setEnabled(connected)
        self.results_list.setEnabled(connected)
        self.add_group_btn.setEnabled(False)
        
        if not connected:
            self.results_list.clear()
    
    def _update_status(self, message: str, is_error: bool = False):
        """Update status label with message and appropriate color."""
        self.status_label.setText(message)
        color = COLORS['error'] if is_error else COLORS['success']
        self.status_label.setStyleSheet(f'color: {color}')
    
    def on_domain_changed(self, index):
        """Handle domain controller selection change."""
        domain = self.domain_combo.currentText()
        logger.info(f'Domain selected: {domain}')
        
        success, message = self.ldap_client.disconnect()
        if success:
            self._update_status(StatusMessage.DISCONNECTED)
            self._update_ui_state(False)
        else:
            self._update_status(message, True)
            QMessageBox.warning(self, "Disconnect Error", 
                              f"An error occurred during disconnection. You may need to restart the app if issues persist.\nError: {message}")
    
    def on_connect(self):
        """Handle connect/disconnect button click."""
        if self.ldap_client.is_connected():
            success, message = self.ldap_client.disconnect()
            if success:
                self._update_status(StatusMessage.DISCONNECTED)
                self._update_ui_state(False)
                self.connect_btn.setText('Connect')
            else:
                self._update_status(message, True)
                QMessageBox.critical(self, "Connection Error", f"Error disconnecting: {message}")
        else:
            domain = self.domain_combo.currentText()
            username = self.username_input.text()
            password = self.password_input.text()
            
            if not all([domain, username, password]):
                QMessageBox.warning(self, "Input Error", 
                                  "Please enter domain controller, username, and password.")
                return
            
            success, message = self.ldap_client.connect(domain, username, password)
            if success:
                self._update_status(StatusMessage.CONNECTED.format(domain, username))
                self._update_ui_state(True)
                self.connect_btn.setText('Disconnect')
            else:
                self._update_status(message, True)
                QMessageBox.critical(self, 'Connection Error', message)
    
    def on_search(self):
        """Handle search button click."""
        search_query = self.search_input.text()
        logger.info(f'Attempting search for query: {search_query}')
        
        self.results_list.clear()
        self.add_group_btn.setEnabled(False)
        
        if not search_query:
            self.results_list.addItem('Please enter a search query')
            return
        
        success, results, message = self.ldap_client.search_users(search_query)
        if success:
            if results:
                for result in results:
                    self.results_list.addItem(result['display_name'])
                    self.results_list.item(self.results_list.count()-1).setData(
                        Qt.UserRole, result['dn'])
            else:
                self.results_list.addItem('No users found.')
        else:
            self._update_status(message, True)
            QMessageBox.critical(self, 'Search Error', message)
    
    def on_result_selected(self):
        """Handle user selection in results list."""
        selected_items = self.results_list.selectedItems()
        self.add_group_btn.setEnabled(bool(selected_items))
    
    def on_add_to_group(self):
        """Handle add to group button click."""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            return
        
        selected_user_dn = selected_items[0].data(Qt.UserRole)
        selected_user_display = selected_items[0].text()
        
        target_group = self.config.get('ad_settings', {}).get('target_group_dn', '')
        if not target_group:
             self._update_status('Status: Target group not configured', True)
             QMessageBox.critical(self, 'Configuration Error', 'Target group DN is not configured in config.json.')
             return
        
        success, message = self.ldap_client.add_user_to_group(selected_user_dn, target_group, user=getpass.getuser())
        if success:
            self._update_status(StatusMessage.ADD_SUCCESS.format(selected_user_display))
            QMessageBox.information(self, 'Success', 
                                  f'Successfully added {selected_user_display} to group')
        else:
            self._update_status(StatusMessage.ADD_FAILED, True)
            QMessageBox.critical(self, 'Add to Group Error', message)

# Note: Base DN and Target Group DN are now read from config.json.
# You need to update config.json with your actual Base DN and the Distinguished Name (DN) of the target group.
# You might also need to adjust search filters and attributes based on your AD schema.

# -----------------------------------------------------------------------------
# CLI Logic
# -----------------------------------------------------------------------------

import getpass

current_user_cli = getpass.getuser()

def cli_connect(args):
    try:
        config = load_config(DEFAULT_CONFIG_PATH)
        if not config:
            sys.exit(1)

        ldap_client = LDAPClient(config)

        target = args.target

        success, message = ldap_client.connect(target)
        if success:
            print(f"Connection to {target} established successfully.")
        else:
            print(f"Connection failed: {message}")

    except Exception as e:
        log_error("connect", args.target, f"Exception during CLI connection: {str(e)}", user=current_user_cli)
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


def cli_addtogroup(args):
    try:
        config = load_config(DEFAULT_CONFIG_PATH)
        if not config:
            sys.exit(1)

        ldap_client = LDAPClient(config)

        user_identifier = args.user
        target_group = args.group

        success, message = ldap_client.add_user_to_group(user_identifier, target_group, user=current_user_cli)

        if success:
            print(f"Successfully added user {user_identifier} to group {target_group}.")
        else:
            print(f"Failed to add user {user_identifier} to group {target_group}: {message}")
            if message != "Operation cancelled by user":
                sys.exit(1)

    except Exception as e:
        log_error("addtogroup", args.group, f"Exception during CLI addtogroup: {str(e)}", user=current_user_cli)
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


def cli_status(args):
    try:
        config = load_config(DEFAULT_CONFIG_PATH)
        if not config:
             sys.exit(1)

        ldap_client = LDAPClient(config)
        status = ldap_client.get_status()
        print(f"Current connection status: {status}")

    except Exception as e:
        log_error("status", "connection", f"Exception during CLI status check: {str(e)}", user=current_user_cli)
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser(description="Active Directory Utility (GUI or CLI)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    connect_parser = subparsers.add_parser("connect", help="Establish an LDAP connection")
    connect_parser.add_argument("--target", required=True, help="Domain controller hostname or IP")
    connect_parser.set_defaults(func=cli_connect)

    add_parser = subparsers.add_parser("addtogroup", help="Add user to group")
    add_parser.add_argument("--user", required=True, help="User identifier (e.g., DN, sAMAccountName) to add")
    add_parser.add_argument("--group", required=True, help="Target group name or DN")
    add_parser.set_defaults(func=cli_addtogroup)

    status_parser = subparsers.add_parser("status", help="Show connection status")
    status_parser.set_defaults(func=cli_status)

    return parser


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, 'command') and args.command is not None:
        if hasattr(args, 'func'):
            args.func(args)
        else:
            parser.print_help()
    else:
        log_info("app_start", "gui", "App started (GUI mode).")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_()) 