
from datetime import datetime
import sqlite3


# ============================
# Function: log_to_database
# ============================
def log_to_database(database_name, level, message, function):
    """
    Log a message to the fb_logging table.
    Parameters:
        database_name (str): Path to the application db.
        level (str): The log level, e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
        message (str): The log message.
        function (str): The name of the function where the log entry was created.

    Returns:
        None
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    # Insert the log entry into the fb_logging table
    try:
        c.execute('INSERT INTO fb_logging (timestamp, level, message, function) VALUES (?, ?, ?, ?)',
                  (datetime.now(), level, message, function))
        conn.commit()
    except Exception as e:
        print(f'Error logging to database: {str(e)}')

    # Close the connection
    conn.close()
