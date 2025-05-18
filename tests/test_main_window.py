import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import MainWindow, LDAPClient

class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create the application instance."""
        cls.app = QApplication(sys.argv)

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'ad_settings': {
                'domain_controllers': ['dc1.example.com', 'dc2.example.com'],
                'base_dn': 'DC=example,DC=com',
                'target_group_dn': 'CN=TestGroup,DC=example,DC=com'
            },
            'logging': {
                'file': 'test.log'
            }
        }
        
        # Mock the config loading
        with patch('main.load_config', return_value=self.config):
            self.window = MainWindow()

    def tearDown(self):
        """Clean up test fixtures."""
        self.window.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up the application instance."""
        cls.app.quit()

    def test_initial_state(self):
        """Test the initial state of the window."""
        # Check if all UI elements are properly initialized
        self.assertEqual(self.window.domain_combo.count(), 2)
        self.assertEqual(self.window.username_input.text(), '')
        self.assertEqual(self.window.password_input.text(), '')
        self.assertEqual(self.window.search_input.text(), '')
        self.assertEqual(self.window.results_list.count(), 0)
        
        # Check if search and add buttons are disabled
        self.assertFalse(self.window.search_btn.isEnabled())
        self.assertFalse(self.window.add_group_btn.isEnabled())
        
        # Check initial status
        self.assertEqual(self.window.status_label.text(), 'Status: Not connected')

    def test_domain_changed(self):
        """Test domain controller selection change."""
        # Mock LDAP client disconnect
        self.window.ldap_client.disconnect = Mock(return_value=(True, 'Successfully disconnected'))
        
        # Change domain
        self.window.domain_combo.setCurrentIndex(1)
        
        # Check if disconnect was called
        self.window.ldap_client.disconnect.assert_called_once()
        
        # Check UI state
        self.assertFalse(self.window.search_btn.isEnabled())
        self.assertFalse(self.window.add_group_btn.isEnabled())
        self.assertEqual(self.window.status_label.text(), 'Status: Disconnected')

    @patch('main.LDAPClient.connect')
    def test_connect_success(self, mock_connect):
        """Test successful connection."""
        # Setup mock
        mock_connect.return_value = (True, 'Successfully connected')
        
        # Set credentials
        self.window.domain_combo.setCurrentIndex(0)
        self.window.username_input.setText('testuser')
        self.window.password_input.setText('testpass')
        
        # Click connect button
        self.window.on_connect()
        
        # Check if connect was called with correct parameters
        mock_connect.assert_called_once_with('dc1.example.com', 'testuser', 'testpass')
        
        # Check UI state
        self.assertTrue(self.window.search_btn.isEnabled())
        self.assertTrue(self.window.search_input.isEnabled())
        self.assertEqual(self.window.connect_btn.text(), 'Disconnect')

    @patch('main.LDAPClient.connect')
    def test_connect_failure(self, mock_connect):
        """Test failed connection."""
        # Setup mock
        mock_connect.return_value = (False, 'Connection failed')
        
        # Set credentials
        self.window.domain_combo.setCurrentIndex(0)
        self.window.username_input.setText('testuser')
        self.window.password_input.setText('testpass')
        
        # Click connect button
        self.window.on_connect()
        
        # Check UI state
        self.assertFalse(self.window.search_btn.isEnabled())
        self.assertFalse(self.window.search_input.isEnabled())
        self.assertEqual(self.window.connect_btn.text(), 'Connect')

    @patch('main.LDAPClient.search_users')
    def test_search_success(self, mock_search):
        """Test successful user search."""
        # Setup mock
        mock_search.return_value = (True, [
            {'display_name': 'user1', 'dn': 'CN=User1,DC=example,DC=com'},
            {'display_name': 'user2', 'dn': 'CN=User2,DC=example,DC=com'}
        ], 'Found 2 results')
        
        # Set connection state
        self.window.ldap_client.connection = MagicMock()
        self.window.ldap_client.connection.bound = True
        
        # Set search query
        self.window.search_input.setText('user')
        
        # Click search button
        self.window.on_search()
        
        # Check results
        self.assertEqual(self.window.results_list.count(), 2)
        self.assertEqual(self.window.results_list.item(0).text(), 'user1')
        self.assertEqual(self.window.results_list.item(0).data(Qt.UserRole), 
                        'CN=User1,DC=example,DC=com')

    @patch('main.LDAPClient.add_user_to_group')
    def test_add_to_group_success(self, mock_add):
        """Test successful user addition to group."""
        # Setup mock
        mock_add.return_value = (True, 'Successfully added user to group')
        
        # Set connection state
        self.window.ldap_client.connection = MagicMock()
        self.window.ldap_client.connection.bound = True
        
        # Add test user to results
        self.window.results_list.addItem('testuser')
        self.window.results_list.item(0).setData(Qt.UserRole, 'CN=TestUser,DC=example,DC=com')
        
        # Select user
        self.window.results_list.setCurrentRow(0)
        
        # Click add to group button
        self.window.on_add_to_group()
        
        # Check if add was called with correct parameters
        mock_add.assert_called_once_with('CN=TestUser,DC=example,DC=com')
        
        # Check status
        self.assertEqual(self.window.status_label.text(), 
                        'Status: Added testuser to group (success)')

if __name__ == '__main__':
    unittest.main() 