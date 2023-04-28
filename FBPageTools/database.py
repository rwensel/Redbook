import sqlite3
import time

from dblogging import log_to_database


# ============================
# Function: create_tables
# ============================
def create_tables(database_name):
    """
    Create tables for storing posts, comments, quotes, and logs if they don't already exist in the database.

    Parameters:
        database_name (str): Path to the application db

    Returns:
        None
    """

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in create_tables: {str(e)}', 'create_tables')
        # Create Facebook logging table
        try:
            c.execute('''
                CREATE TABLE IF NOT EXISTS "fb_logging" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    level TEXT,
                    message TEXT,
                    function TEXT
                )''')
        except Exception as e:
            print(f'Error in create_tables: {str(e)}')

    #  Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering create_tables function', 'create_tables')

    #  Create memes table
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS posts
                            (id TEXT PRIMARY KEY,
                            permalink TEXT,
                            title TEXT,
                            author TEXT,
                            ups INTEGER,
                            created_utc INTEGER,
                            image_link TEXT,
                            indexed_time INTEGER,
                            posted INTEGER)''')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in create_tables: {str(e)}', 'create_tables')

    #  Create quotes table
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS "quotes" (
            "author"	TEXT,
            "quote"	TEXT,
            "postedOn"	INTEGER,
            "posted"	INTEGER DEFAULT 0
        )''')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in create_tables: {str(e)}', 'create_tables')

    #  Create Facebook Post table
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS "fb_posts" (
            "post_id"	TEXT,
            "message"	TEXT,
            "created_time"	INTEGER,
            "indexed_time"	INTEGER,
            PRIMARY KEY("post_id")
        )''')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in create_tables: {str(e)}', 'create_tables')

    #  Create Facebook Comments table
    try:
        c.execute('''
        CREATE TABLE IF NOT EXISTS "fb_comments" (
            "comment_id"	TEXT,
            "post_id"	TEXT,
            "message"	TEXT,
            "created_time"	INTEGER,
            "indexed_time"	INTEGER,
            "openai_text"	TEXT,
            "postedOn"	INTEGER,
            "completed"	INTEGER DEFAULT 0
        )''')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in create_tables: {str(e)}', 'create_tables')

    # Commit and close the connection
    try:
        conn.commit()
        conn.close()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in create_tables: {str(e)}', 'create_tables')

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting create_tables function', 'create_tables')


# ============================
# Function: update_table_post_status
# ============================
def update_table_post_status(database_name, table, row):
    """
    Update table rows when item has been posted to prevent reposting.

    Parameters:
        table (str): The name of the table to update
        row (list): the row id to mark as posted
        database_name (str): Path to the application db.

    Returns:
        None
    """
    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering update_table_post_status function', 'update_table_post_status')

    # Connect to the SQLite database
    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    # Check if the table is 'memes'
    if 'memes' in table:
        c.execute(f'UPDATE {table} SET posted = 1, postedOn = {int(time.time())} WHERE id = ?', (row[0][0],))
        log_to_database(database_name, 'INFO', f'Updated {row[0][0]} to posted 1', 'update_table_post_status')

    # Check if the table is 'quotes'
    elif 'quotes' in table:
        c.execute(f'UPDATE {table} SET posted = 1, postedOn = {int(time.time())} WHERE quote = ?', (row[0][1],))
        log_to_database(database_name, 'INFO', f'Updated {row[0][1]} to posted 1', 'update_table_post_status')

    # Commit the changes to the database
    conn.commit()

    # Close the connection
    conn.close()

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting update_table_post_status function', 'update_table_post_status')
