import unittest
from unittest.mock import Mock, patch
from ldap3 import Server, Connection, SAFE_SYNC, SUBTREE, ALL
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError, LDAPException
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import LDAPClient

class TestLDAPClient(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'ad_settings': {
                'domain_controllers': ['dc1.example.com', 'dc2.example.com'],
                'base_dn': 'DC=example,DC=com',
                'target_group_dn': 'CN=TestGroup,DC=example,DC=com'
            }
        }
        self.client = LDAPClient(self.config)

    @patch('ldap3.Server')
    @patch('ldap3.Connection')
    def test_connect_success(self, mock_connection, mock_server):
        """Test successful connection to LDAP server."""
        # Setup mock
        mock_conn = Mock()
        mock_conn.bound = True
        mock_connection.return_value = mock_conn

        # Test connection
        success, message = self.client.connect('dc1.example.com', 'user', 'pass')

        # Assertions
        self.assertTrue(success)
        self.assertIn('Successfully connected', message)
        self.assertEqual(self.client.connection, mock_conn)

    @patch('ldap3.Server')
    @patch('ldap3.Connection')
    def test_connect_bind_error(self, mock_connection, mock_server):
        """Test connection with authentication error."""
        # Setup mock
        mock_connection.side_effect = LDAPBindError('Invalid credentials')

        # Test connection
        success, message = self.client.connect('dc1.example.com', 'user', 'pass')

        # Assertions
        self.assertFalse(success)
        self.assertIn('Authentication failed', message)
        self.assertIsNone(self.client.connection)

    @patch('ldap3.Server')
    @patch('ldap3.Connection')
    def test_connect_socket_error(self, mock_connection, mock_server):
        """Test connection with network error."""
        # Setup mock
        mock_connection.side_effect = LDAPSocketOpenError('Connection refused')

        # Test connection
        success, message = self.client.connect('dc1.example.com', 'user', 'pass')

        # Assertions
        self.assertFalse(success)
        self.assertIn('Server unreachable', message)
        self.assertIsNone(self.client.connection)

    def test_disconnect_not_connected(self):
        """Test disconnecting when not connected."""
        success, message = self.client.disconnect()
        self.assertTrue(success)
        self.assertEqual(message, 'Not connected')

    @patch('ldap3.Connection')
    def test_disconnect_success(self, mock_connection):
        """Test successful disconnection."""
        # Setup mock
        mock_conn = Mock()
        self.client.connection = mock_conn

        # Test disconnection
        success, message = self.client.disconnect()

        # Assertions
        self.assertTrue(success)
        self.assertEqual(message, 'Successfully disconnected')
        self.assertIsNone(self.client.connection)
        mock_conn.unbind.assert_called_once()

    @patch('ldap3.Connection')
    def test_search_users_success(self, mock_connection):
        """Test successful user search."""
        # Setup mock
        mock_conn = Mock()
        mock_conn.bound = True
        mock_conn.result = {'description': 'success'}
        mock_conn.entries = [
            Mock(sAMAccountName=Mock(value='user1'), 
                 cn=Mock(value='User One'),
                 distinguishedName=Mock(value='CN=User One,DC=example,DC=com')),
            Mock(sAMAccountName=Mock(value='user2'),
                 cn=Mock(value='User Two'),
                 distinguishedName=Mock(value='CN=User Two,DC=example,DC=com'))
        ]
        self.client.connection = mock_conn

        # Test search
        success, results, message = self.client.search_users('user')

        # Assertions
        self.assertTrue(success)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['display_name'], 'user1')
        self.assertEqual(results[0]['dn'], 'CN=User One,DC=example,DC=com')
        self.assertIn('Found 2 results', message)

    @patch('ldap3.Connection')
    def test_search_users_no_results(self, mock_connection):
        """Test user search with no results."""
        # Setup mock
        mock_conn = Mock()
        mock_conn.bound = True
        mock_conn.result = {'description': 'success'}
        mock_conn.entries = []
        self.client.connection = mock_conn

        # Test search
        success, results, message = self.client.search_users('nonexistent')

        # Assertions
        self.assertTrue(success)
        self.assertEqual(len(results), 0)
        self.assertIn('Found 0 results', message)

    @patch('ldap3.Connection')
    def test_add_user_to_group_success(self, mock_connection):
        """Test successful user addition to group."""
        # Setup mock
        mock_conn = Mock()
        mock_conn.bound = True
        mock_conn.result = {'description': 'success'}
        self.client.connection = mock_conn

        # Test add to group
        success, message = self.client.add_user_to_group('CN=User,DC=example,DC=com')

        # Assertions
        self.assertTrue(success)
        self.assertIn('Successfully added', message)
        mock_conn.modify.assert_called_once()

    @patch('ldap3.Connection')
    def test_add_user_to_group_failure(self, mock_connection):
        """Test failed user addition to group."""
        # Setup mock
        mock_conn = Mock()
        mock_conn.bound = True
        mock_conn.result = {
            'description': 'error',
            'diagnostic_message': 'User already in group'
        }
        self.client.connection = mock_conn

        # Test add to group
        success, message = self.client.add_user_to_group('CN=User,DC=example,DC=com')

        # Assertions
        self.assertFalse(success)
        self.assertIn('Add to group failed', message)
        mock_conn.modify.assert_called_once()

if __name__ == '__main__':
    unittest.main() 