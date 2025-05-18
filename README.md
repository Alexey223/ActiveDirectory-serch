# Active Directory Utility

This project is a prototype for a graphical utility to manage Active Directory groups, with a focus on building a robust, auditable, and scalable application structure, even for local use.

## Features

-   **GUI Interface**: User-friendly graphical interface for connecting, searching, and adding users to groups.
-   **CLI Interface**: Command-line interface for performing operations programmatically.
-   **Auditable Logging**: Logs all significant actions in a structured JSON format.
-   **Secure Configuration**: Uses `.env` file for sensitive credentials.
-   **Protected Groups**: Implements a confirmation step for adding users to predefined sensitive groups.
-   **Modular Design**: Separates UI, business logic, and logging into distinct modules.

## Project Structure

```
project_root/
│
├── main.py                 # Entry point, handles GUI and CLI mode selection
├── ldapclient.py           # Business logic for LDAP operations (connect, add user, etc.)
├── logger_setup.py         # Centralized logging configuration (JSON to file, formatted to stdout)
├── sensitive_groups.json   # Configuration for sensitive/protected AD groups
├── .env.example            # Example file for environment variables (credentials)
├── config.json             # Main application configuration (AD settings, logging file path)
├── logs/                   # Directory for log files
│   └── activity.log        # JSON activity log
└── tests/                  # Unit tests
    ├── test_cli.py         # Tests for CLI functions
    ├── test_ldap_client.py # Tests for LDAPClient class
    └── test_main_window.py # Tests for GUI (MainWindow) class
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `requirements.txt` is not yet created, but this is the standard step. You would typically generate this file using `pip freeze > requirements.txt` after installing necessary libraries like `PyQt5`, `python-ldap3`, `python-dotenv`, `pytest`, etc.)*

5.  **Configure Environment Variables:**
    -   Create a file named `.env` in the project root.
    -   Copy the contents of `.env.example` into `.env` and replace the placeholder values with your actual LDAP credentials.
    ```dotenv
    # .env
    LDAP_USER=cn=admin,dc=example,dc=com
    LDAP_PASSWORD=somesecretpassword123
    ```
    *(\*\*Never commit your `.env` file with actual credentials to the repository!\*\*)*

6.  **Configure Application Settings:**
    -   Update the `config.json` file with your specific Active Directory settings, including domain controllers, base DN, target group DN, and desired log file path.
    ```json
    // config.json
    {
      "ad_settings": {
        "domain_controllers": ["your_dc1.domain.com", "your_dc2.domain.com"],
        "base_dn": "DC=yourdomain,DC=com",
        "target_group_dn": "CN=YourTargetGroup,OU=Groups,DC=yourdomain,DC=com"
      },
      "logging": {
        "file": "ad_utility.log"
      }
    }
    ```

7.  **Configure Sensitive Groups (Optional):**
    -   Modify `sensitive_groups.json` to include the names of any groups that should require user confirmation before adding members.
    ```json
    // sensitive_groups.json
    {
      "protected_groups": [
        "Domain Admins",
        "Enterprise Admins",
        "Schema Admins"
      ]
    }
    ```

## Usage

This application can be run in either GUI or CLI mode.

### GUI Mode

To launch the graphical interface, simply run `main.py` without any command-line arguments:

```bash
python main.py
```

The GUI allows you to select a domain controller (from `config.json`), enter credentials (loaded from `.env`), connect to LDAP, search for users, and add selected users to the target group (defined in `config.json`).

### CLI Mode

To use the command-line interface, run `main.py` with specific commands and arguments. Use `-h` or `--help` with `main.py` or any command for usage details.

```bash
python main.py -h
python main.py [command] -h
```

Available commands:

-   **`connect`**: Establish a connection to a specified domain controller.
    ```bash
    python main.py connect --target your_dc1.domain.com
    ```

-   **`addtogroup`**: Add a user to a specified group.
    ```bash
    python main.py addtogroup --user "CN=John Doe,OU=Users,DC=yourdomain,DC=com" --group "CN=YourTargetGroup,OU=Groups,DC=yourdomain,DC=com"
    # Note: The --user and --group arguments currently expect the Distinguished Name (DN).
    # The 'group' argument for sensitive group check uses the simple name defined in sensitive_groups.json.
    ```
    *If the target group is listed in `sensitive_groups.json`, you will be prompted for confirmation.*\n
-   **`status`**: Show the current connection status.
    ```bash
    python main.py status
    ```

## Logging

All significant actions (connect attempts, add attempts, etc.) are logged in JSON format to the file specified in `config.json` (defaults to `logs/activity.log`). Information logged includes timestamp, user (system user), action, target object, status (success/failure/cancelled), and a message.

Check this file to audit operations performed by the application.

## Running Tests

To run the unit tests (requires `pytest`):

```bash
pytest tests/
```

## Future Enhancements

-   Implement actual LDAP operations in `ldapclient.py`.
-   Add more comprehensive error handling.
-   Improve user feedback in the GUI.
-   Implement user authentication and authorization beyond local system user.
-   Integrate with CI/CD pipelines (e.g., GitHub Actions).
-   Containerization (e.g., Docker).
-   More advanced configuration management.

---

*This README provides instructions for the current state of the prototype. Remember that actual LDAP connectivity requires a reachable domain controller and valid credentials.* 