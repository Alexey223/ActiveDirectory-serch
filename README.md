# Active Directory Utility (Arcelor Project)

This is a graphical utility application developed with Python and PyQt5 to manage Active Directory users within a corporate environment, focusing on tasks like searching users and adding them to specific groups.

## Features

*   Connect to a specified Domain Controller.
*   Authenticate with provided credentials.
*   Search for users in Active Directory.
*   Add selected users to a pre-configured AD group.
*   Basic logging for auditing purposes.
*   Modern dark UI theme.

## Prerequisites

*   Python 3.6+
*   Access to an Active Directory environment (for full functionality).

## Installation

1.  Clone this repository:

    ```bash
    git clone <repository_url>
    cd Arcelor-project-ActiveDirectory-Auto-Inet-Group
    ```

2.  (Optional) Create a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
    ```

3.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4.  Download necessary SVG icons:

    Create a folder named `icons` in the project root and place the following SVG files inside it:
    *   `connect_icon.svg`
    *   `search_icon.svg`
    *   `add_icon.svg`

## Configuration

Update the `config.json` file in the project root with your Active Directory settings:

```json
{
  "ad_settings": {
    "base_dn": "DC=example,DC=com",       /* Replace with your Base DN */
    "target_group_dn": "CN=KRR-LG-InetUsers,OU=Groups,DC=example,DC=com", /* Replace with your Target Group DN */
    "domain_controllers": ["your_dc1.example.com", "your_dc2.example.com"] /* Optional: List of DCs */
  },
  "logging": {
    "file": "ad_utility.log" /* Path for log file */
  }
}
```

## Running the Application

```bash
python main.py
```

## Task Management (using Task Master)

This project uses Task Master for managing development tasks. Refer to the Task Master documentation for details on how to use it with this project.

## Contributing

(Add contributing guidelines here if applicable)

## License

(Add license information here) 