import sys
import logging
import json
import os
import ldap3 # Add direct import for the ldap3 module
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QComboBox, QLineEdit, QVBoxLayout, QWidget, QListWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QByteArray, QEasingCurve
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from ldap3 import Server, Connection, SAFE_SYNC, SUBTREE, ALL # Re-add this import
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError, LDAPException

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

def load_config(config_path='config.json'):
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

        self.config = load_config() # Load configuration

        if not self.config:
             sys.exit(1) # Exit if config loading failed

        # Configure file logging based on config
        log_file = self.config.get('logging', {}).get('file', 'ad_utility.log')
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(file_handler)
            logger.info(f"File logging configured to {log_file}")
        except Exception as e:
            logger.error(f"Failed to configure file logging to {log_file}: {e}")
            QMessageBox.warning(self, "Logging Warning", f"Failed to configure file logging to {log_file}: {e}. Logging will only be to console.")

        # Apply modern stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212; /* Very dark background (main) */
                color: #E0E0E0; /* Light gray text (primary) */
                font-family: "Segoe UI", "Roboto", sans-serif; /* Modern font */
                font-size: 14px;
            }

            QWidget {
                padding: 15px; /* Increased padding to the main widget */
            }

            QLabel {
                color: #E0E0E0; /* Light gray text (primary) */
                font-size: 14px;
                margin-bottom: 4px; /* Space below labels */
                font-weight: 500; /* Slightly bolder labels */
            }

            QLineEdit, QComboBox, QListWidget {
                background-color: #1E1E1E; /* Darker gray surface */
                color: #E0E0E0; /* Light gray text */
                border: 1px solid #A0A0A0; /* Medium gray border */
                border-radius: 5px; /* Rounded corners */
                padding: 8px; /* Increased padding */
                selection-background-color: #81D8D0; /* Tiffany accent for selection */
                selection-color: #1E1E1E; /* Dark text on accent selection */
                margin-bottom: 10px; /* Space below inputs */
                outline: none; /* Remove focus outline */
                /* Transition for border color */
                transition: border-color 0.3s ease-in-out; /* Ensure transition is present */
            }

            QLineEdit:focus, QComboBox:focus, QListWidget:focus {
                 border-color: #81D8D0; /* Tiffany highlight border on focus */
            }

            QComboBox::drop-down {
                border: 0px; /* Remove default dropdown border */
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
            }

            QComboBox::down-arrow {
                image: url(icons/down_arrow_A0A0A0.png); /* Placeholder for medium gray custom arrow */
                width: 12px;
                height: 12px;
            }

            QPushButton {
                background-color: #81D8D0; /* Tiffany accent color for primary actions */
                color: #121212; /* Very dark text on accent */
                border: none; /* No border */
                border-radius: 5px;
                padding: 10px 20px; /* Increased padding */
                min-width: 120px; /* Wider buttons */
                margin-top: 5px; /* Space above buttons */
                margin-bottom: 10px; /* Space below buttons */
                font-weight: bold;
                text-align: left; /* Align text to the left for icon spacing */
                padding-left: 15px; /* Add padding for icon */
                icon-size: 20px 20px; /* Set a default icon size */
                /* Transition for background color */
                transition: background-color 0.3s ease-in-out; /* Ensure transition is present */
            }

            QPushButton:hover {
                background-color: #A0E0D8; /* Pale Tiffany on hover */
                color: #1E1E1E; /* Darker text on pale accent */
            }

            QPushButton:pressed {
                background-color: #61B8B0; /* Slightly darker Tiffany on press */
            }

            QPushButton:disabled {
                background-color: #1E1E1E; /* Dark background when disabled */
                color: #A0A0A0; /* Medium gray text when disabled */
                border: none;
            }

            QListWidget {
                margin-top: 8px; /* Space above list */
                border: 1px solid #A0A0A0; /* Medium gray border */
                border-radius: 5px;
            }

            QListWidget::item {
                 padding: 8px 5px; /* Padding for list items */
                 border-bottom: 1px solid #1E1E1E; /* Separator line same as surface */
            }

            QListWidget::item:last {
                 border-bottom: none; /* No border for the last item */
            }

             QListWidget::item:selected {
                 background-color: #81D8D0; /* Tiffany highlight selected item */
                 color: #1E1E1E; /* Dark text on accent */
            }

            /* Styles for the status label */
            QLabel#status_label {
                font-weight: bold;
                margin-top: 10px; /* Space above status */
                margin-bottom: 5px; /* Space below status */
                font-size: 13px; /* Slightly smaller font */
            }

            /* Specific status colors (will be set in code) */
            QLabel#status_label[style*="color: green"] {
                color: #81C784; /* Success color (Green) */
            }
            QLabel#status_label[style*="color: red"] {
                color: #E57373; /* Error color (Red) */
            }
            QLabel#status_label[style*="color: gray"] {
                color: #A0A0A0; /* Default/disconnected color (Medium Gray) */
            }

        """)

        self.setWindowTitle('Active Directory Utility')
        self.setGeometry(100, 100, 600, 650) # Adjusted height slightly
        logger.info('GUI started: Active Directory Utility') # Use logger instead of logging.info

        self.connection = None # Store the LDAP connection
        # Use domain controllers from config or default
        self.domain_controllers = self.config.get('ad_settings', {}).get('domain_controllers', ["dc1.example.com", "dc2.example.com"])

        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget) # Re-added layout definition

        # Domain controller dropdown
        domain_layout = QVBoxLayout()
        self.domain_label = QLabel('Domain Controller:')
        domain_layout.addWidget(self.domain_label)
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(self.domain_controllers)
        self.domain_combo.currentIndexChanged.connect(self.on_domain_changed)
        domain_layout.addWidget(self.domain_combo)
        layout.addLayout(domain_layout)

        # Username and Password fields
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

        # Connect button
        self.connect_btn = QPushButton('Connect')
        # Load and set icon for Connect button, recolored to primary text color
        try:
            connect_icon = load_svg_icon('icons/connect_icon.svg', color='#E0E0E0', size=QSize(20, 20)) # Use helper function
            self.connect_btn.setIcon(connect_icon)
            # Icon size is now handled by the stylesheet icon-size property or the size parameter in load_svg_icon
            # self.connect_btn.setIconSize(self.connect_btn.sizeHint() * 0.8) # Removed
        except Exception as e:
             logger.warning(f"Could not load connect icon: {e}")

        self.connect_btn.clicked.connect(self.on_connect)
        layout.addWidget(self.connect_btn)

        # Status label
        self.status_label = QLabel('Status: Not connected')
        self.status_label.setObjectName('status_label') # Set object name for specific styling
        self.status_label.setStyleSheet('color: gray')
        layout.addWidget(self.status_label)

        layout.addSpacing(20)

        # User Search section
        search_layout = QVBoxLayout()
        self.search_label = QLabel('Search User:')
        search_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton('Search')
        # Load and set icon for Search button, recolored to primary text color
        try:
            search_icon = load_svg_icon('icons/search_icon.svg', color='#E0E0E0', size=QSize(20, 20)) # Use helper function
            self.search_btn.setIcon(search_icon)
            # Icon size is now handled by the stylesheet icon-size property or the size parameter in load_svg_icon
            # self.search_btn.setIconSize(self.search_btn.sizeHint() * 0.8) # Removed
        except Exception as e:
            logger.warning(f"Could not load search icon: {e}")

        self.search_btn.clicked.connect(self.on_search)
        # Disable search until connected
        self.search_btn.setEnabled(False)
        search_layout.addWidget(self.search_btn)

        # Search results list and Add button
        results_layout = QHBoxLayout()

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.on_result_selected)
        results_layout.addWidget(self.results_list)

        # Add to Group button
        self.add_group_btn = QPushButton('Add to KRR-LG-InetUsers')
         # Load and set icon for Add Group button, recolored to primary text color
        try:
            add_icon = load_svg_icon('icons/add_icon.svg', color='#121212', size=QSize(20, 20)) # Use helper function, color set to background for contrast on accent button
            self.add_group_btn.setIcon(add_icon)
            # Icon size is now handled by the stylesheet icon-size property or the size parameter in load_svg_icon
            # self.add_group_btn.setIconSize(self.add_group_btn.sizeHint() * 0.8) # Removed
        except Exception as e:
            logger.warning(f"Could not load add icon: {e}")

        self.add_group_btn.setEnabled(False) # Disable initially
        self.add_group_btn.clicked.connect(self.on_add_to_group)
        results_layout.addWidget(self.add_group_btn)
        results_layout.setStretchFactor(self.results_list, 3)
        results_layout.setStretchFactor(self.add_group_btn, 1)

        search_layout.addLayout(results_layout)
        layout.addLayout(search_layout)

        # Disable search and add group sections initially
        self.search_label.setEnabled(False)
        self.search_input.setEnabled(False)
        self.search_btn.setEnabled(False) # Also disable the search button
        self.results_list.setEnabled(False)

    def on_domain_changed(self, index):
        domain = self.domain_combo.currentText()
        logger.info(f'Domain selected: {domain}') # Use logger instead of logging.info
        self.status_label.setText(f'Status: Selected {domain}')
        self.status_label.setStyleSheet('color: gray') # Update style color
        # Disconnect if already connected when changing domain
        if self.connection:
            try:
                self.connection.unbind()
                self.connection = None
                self.status_label.setText('Status: Disconnected')
                self.status_label.setStyleSheet('color: gray') # Update style color
                logger.info("Disconnected from AD.")
                # Enable search and add group sections on successful disconnection
                self.search_label.setEnabled(False)
                self.search_input.setEnabled(False)
                self.search_btn.setEnabled(False)
                self.results_list.setEnabled(False)
                self.add_group_btn.setEnabled(False)
                self.results_list.clear()
            except Exception as e:
                 logger.error(f"Error during disconnect: {e}")
                 # Even if disconnect fails, assume connection is broken for UI purposes
                 self.connection = None
                 self.status_label.setText('Status: Disconnected (Error)')
                 self.status_label.setStyleSheet('color: red') # Update style color
                 QMessageBox.warning(self, "Disconnect Error", f"An error occurred during disconnection. You may need to restart the app if issues persist.\nError: {e}")


    def on_connect(self):
        if self.connection and self.connection.bound:
            try:
                self.connection.unbind()
                self.connection = None
                self.status_label.setText('Status: Disconnected')
                self.status_label.setStyleSheet('color: gray') # Update style color
                logger.info("Disconnected from AD.")
                # Enable search and add group sections on successful disconnection
                self.search_label.setEnabled(False)
                self.search_input.setEnabled(False)
                self.search_btn.setEnabled(False)
                self.results_list.setEnabled(False)
                self.add_group_btn.setEnabled(False)
                self.results_list.clear()
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
                self.status_label.setText('Status: Connection error')
                self.status_label.setStyleSheet('color: red') # Update style color
                QMessageBox.critical(self, "Connection Error", f"Error disconnecting: {e}")
        else:
            domain = self.domain_combo.currentText()
            username = self.username_input.text()
            password = self.password_input.text()
            logger.info(f'Attempting to connect to {domain} as {username}') # Use logger instead of logging.info

            if not domain or not username or not password:
                QMessageBox.warning(self, "Input Error", "Please enter domain controller, username, and password.")
                logger.warning("Connection attempt failed: Missing input fields.")
                return

            try:
                server = Server(domain, use_ssl=True, get_info=ALL)
                conn = Connection(server, user=username, password=password, client_strategy=SAFE_SYNC, auto_bind=True)

                if conn.bound:
                    self.connection = conn
                    self.status_label.setText(f'Status: Connected to {domain} as {username}')
                    self.status_label.setStyleSheet('color: green') # Update style color
                    logger.info(f'Successfully connected to {domain} as {username}')
                    # Enable search and add group sections on successful connection
                    self.search_label.setEnabled(True)
                    self.search_input.setEnabled(True)
                    self.search_btn.setEnabled(True)
                    self.results_list.setEnabled(True)
                else:
                    # More specific error details from conn.result
                    error_code = conn.result.get('result', 'N/A')
                    error_desc = conn.result.get('description', 'Unknown error')
                    error_diag = conn.result.get('diagnostic_message', 'N/A')
                    full_error = f"Code: {error_code}, Desc: {error_desc}, Diag: {error_diag}"
                    logger.error(f'Connection failed for {username} to {domain}: {full_error}')
                    self.status_label.setText('Status: Connection failed')
                    self.status_label.setStyleSheet('color: red') # Update style color
                    QMessageBox.critical(self, 'Connection Failed', f'Failed to connect to {domain}. Check credentials and server address.\nError: {error_desc}\nDetails: {error_diag}')

            except LDAPBindError as e:
                logger.error(f'LDAP Bind Error during connection to {domain}: {e}')
                self.status_label.setText('Status: Authentication failed')
                self.status_label.setStyleSheet('color: red') # Update style color
                QMessageBox.critical(self, 'Authentication Failed', f'Authentication failed for user {username}. Check your credentials.\nError: {e}')
            except LDAPSocketOpenError as e:
                 logger.error(f'LDAP Socket Open Error during connection to {domain}: {e}')
                 self.status_label.setText('Status: Server unreachable')
                 self.status_label.setStyleSheet('color: red') # Update style color
                 QMessageBox.critical(self, 'Server Unreachable', f'Could not connect to domain controller {domain}. Check the server address and network connectivity.\nError: {e}')
            except ldap3.core.exceptions.LDAPException as e: # Catch base LDAP exception for other connection errors
                 logger.error(f'An LDAP exception occurred during connection to {domain}: {e}')
                 self.status_label.setText('Status: Connection error')
                 self.status_label.setStyleSheet('color: red') # Update style color
                 QMessageBox.critical(self, 'Connection Error', f'An LDAP exception occurred during connection.\nError: {e}')
            except Exception as e:
                self.status_label.setText('Status: Connection error')
                self.status_label.setStyleSheet('color: red') # Update style color
                logger.error(f'An unexpected error occurred during connection to {domain}: {e}')
                QMessageBox.critical(self, 'Connection Error', f'An unexpected error occurred during connection.\nError: {e}')

    def on_search(self):
        search_query = self.search_input.text()
        logger.info(f'Attempting search for query: {search_query}') # Use logger instead of logging.info

        self.results_list.clear()
        self.add_group_btn.setEnabled(False)

        if not self.connection or not self.connection.bound:
            self.status_label.setText('Status: Not connected')
            self.status_label.setStyleSheet('color: red') # Update style color
            logger.warning('Search attempted while not connected.')
            QMessageBox.warning(self, 'Not Connected', 'Please connect to a domain controller first.')
            return

        if not search_query:
             self.results_list.addItem('Please enter a search query')
             logger.warning('Search attempted with empty query.')
             return

        # Read Base DN from config
        base_dn = self.config.get('ad_settings', {}).get('base_dn', '')
        if not base_dn:
            logger.error("Base DN not configured in config.json")
            QMessageBox.critical(self, "Configuration Error", "Base DN is not configured in config.json.")
            return

        try:
            search_filter = f'(|(sAMAccountName=*{search_query}*)(cn=*{search_query}*))'

            logger.info(f'Performing LDAP search with filter: {search_filter} on base DN: {base_dn}')
            self.connection.search(base_dn, search_filter, SUBTREE, attributes=['sAMAccountName', 'cn', 'distinguishedName'])

            # Check connection.result for success/failure
            if self.connection.result.get('description') == 'success':
                entries = self.connection.entries
                if entries:
                    logger.info(f'Found {len(entries)} search results for query: {search_query}')
                    for entry in entries:
                         display_name = entry.sAMAccountName.value if entry.sAMAccountName else entry.cn.value
                         self.results_list.addItem(display_name)
                         self.results_list.item(self.results_list.count()-1).setData(Qt.UserRole, entry.distinguishedName.value)
                else:
                    self.results_list.addItem('No users found.')
                    logger.info(f'No users found for query: {search_query}')
            else:
                 # More specific error details from connection.result for search failure
                 error_code = self.connection.result.get('result', 'N/A')
                 error_desc = self.connection.result.get('description', 'Unknown error')
                 error_diag = self.connection.result.get('diagnostic_message', 'N/A')
                 full_error = f"Code: {error_code}, Desc: {error_desc}, Diag: {error_diag}"
                 logger.error(f'LDAP search failed for query {search_query} on {base_dn}: {full_error}')
                 QMessageBox.critical(self, 'Search Failed', f'An error occurred during search.\nError: {error_desc}\nDetails: {error_diag}')

        except ldap3.core.exceptions.LDAPException as e: # Catch base LDAP exception for search errors
             logger.error(f'An LDAP exception occurred during search for query {search_query} on {base_dn}: {e}')
             QMessageBox.critical(self, 'Search Error', f'An LDAP exception occurred during search.\nError: {e}')
        except Exception as e:
            logger.error(f'An unexpected error occurred during LDAP search for query {search_query} on {base_dn}: {e}')
            QMessageBox.critical(self, 'Search Error', f'An unexpected error occurred during search.\nError: {e}')

    def on_result_selected(self):
        selected_items = self.results_list.selectedItems()
        if selected_items:
            selected_user_display = selected_items[0].text()
            selected_user_dn = selected_items[0].data(Qt.UserRole)
            logger.info(f'Result selected: {selected_user_display} (DN: {selected_user_dn})')
            self.add_group_btn.setEnabled(True)
        else:
            logger.info('No result selected')
            self.add_group_btn.setEnabled(False)

    def on_add_to_group(self):
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            logger.warning('Add to group clicked with no user selected.')
            return

        selected_user_display = selected_items[0].text()
        selected_user_dn = selected_items[0].data(Qt.UserRole)

        # Read Target Group DN from config
        target_group_dn = self.config.get('ad_settings', {}).get('target_group_dn', '')
        if not target_group_dn:
            logger.error("Target Group DN not configured in config.json")
            QMessageBox.critical(self, "Configuration Error", "Target Group DN is not configured in config.json.")
            return

        logger.info(f'Attempting to add user {selected_user_dn} to group {target_group_dn}')

        if not self.connection or not self.connection.bound:
            self.status_label.setText('Status: Not connected')
            self.status_label.setStyleSheet('color: red') # Update style color
            logger.warning('Add to group attempted while not connected.')
            QMessageBox.warning(self, 'Not Connected', 'Please connect to a domain controller first.')
            return

        try:
            modification = [(self.connection.MODIFY_ADD, 'member', [selected_user_dn])]
            self.connection.modify(target_group_dn, modification)

            # Check connection.result for success/failure
            if self.connection.result.get('description') == 'success':
                self.status_label.setText(f'Status: Added {selected_user_display} to group (success)')
                self.status_label.setStyleSheet('color: green') # Update style color
                logger.info(f'Successfully added {selected_user_display} to {target_group_dn}')
                QMessageBox.information(self, 'Success', f'Successfully added {selected_user_display} to {target_group_dn}')
            else:
                # More specific error details from connection.result for modify failure
                error_code = self.connection.result.get('result', 'N/A')
                error_desc = self.connection.result.get('description', 'Unknown error')
                error_diag = self.connection.result.get('diagnostic_message', 'N/A')
                full_error = f"Code: {error_code}, Desc: {error_desc}, Diag: {error_diag}"
                logger.error(f'Failed to add {selected_user_display} to {target_group_dn}: {full_error}')
                self.status_label.setText(f'Status: Add to group failed')
                self.status_label.setStyleSheet('color: red') # Update style color
                QMessageBox.critical(self, 'Add to Group Failed', f'Failed to add {selected_user_display} to group.\nError: {error_desc}\nDetails: {error_diag}')

        except ldap3.core.exceptions.LDAPException as e: # Catch base LDAP exception for modify errors
             logger.error(f'An LDAP exception occurred during add to group operation for {selected_user_display} to {target_group_dn}: {e}')
             QMessageBox.critical(self, 'Add to Group Error', f'An LDAP exception occurred during the add to group operation.\nError: {e}')
        except Exception as e:
            logger.error(f'An unexpected error occurred during add to group operation for {selected_user_display} to {target_group_dn}: {e}')
            QMessageBox.critical(self, 'Add to Group Error', f'An unexpected error occurred during the add to group operation.\nError: {e}')

# Note: Base DN and Target Group DN are now read from config.json.
# You need to update config.json with your actual Base DN and the Distinguished Name (DN) of the target group.
# You might also need to adjust search filters and attributes based on your AD schema.

if __name__ == '__main__':
    logger.info('App started...')
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 