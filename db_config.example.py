"""
db_config.example.py
---------------------
Template for db_config.py. Copy this file, rename the copy to
db_config.py, and fill in your real MySQL password.

    cp db_config.example.py db_config.py      (Mac/Linux)
    copy db_config.example.py db_config.py    (Windows)

db_config.py itself is in .gitignore so your real password is
never pushed to GitHub.
"""

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "retail_inventory"
}
