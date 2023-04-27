import os
import re
import sqlite3

import facebook
import openai
import requests
import time


def create_tables(database_name):
    """
    Create tables for storing posts, comments, quotes, and logs if they don't already exist in the database.

    Parameters:
        database_name (str): Path to the application db

    Returns:
        None
    """

    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    #  Create quotes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS "quotes" (
        "author"	TEXT,
        "quote"	TEXT,
        "postedOn"	INTEGER,
        "posted"	INTEGER DEFAULT 0
    )''')

    #  Create Log table
    c.execute('''
        CREATE TABLE IF NOT EXISTS "fb_tools_log" (
        "asctime"	INTEGER,
        "levelname"	TEXT,
        "message"	TEXT,
        "module"	TEXT
    )''')

    #  Create Facebook Post table
    c.execute('''
        CREATE TABLE IF NOT EXISTS "fb_posts" (
        "post_id"	TEXT,
        "message"	TEXT,
        "created_time"	INTEGER,
        "indexed_time"	INTEGER,
        PRIMARY KEY("post_id")
    )''')

    #  Create Facebook Comments table
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

    conn.commit()
    conn.close()


def get_all_comments(database_name, post_id, access_token):
    """
    Retrieve comment for a given post and store them in the database.

    Parameters:
        post_id (str): The ID of the post to retrieve comments for.
        access_token (str): The access token to use for the Graph API.
        database_name (str): Path to the application db.

    Returns:
        None
    """

    graph = facebook.GraphAPI(access_token)

    comments = graph.get_object(post_id + '/comments')

    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    for comment in comments['data']:
        comment_id = comment['id']
        message = comment.get('message', '')
        created_time = comment['created_time']

        # Check if comment already exists in the database
        c.execute('SELECT comment_id FROM fb_comments WHERE comment_id = ? AND message = ?', (comment_id, message))
        existing_comment = c.fetchone()

        if existing_comment is None:
            c.execute('INSERT INTO fb_comments (comment_id, post_id, message, created_time, indexed_time) VALUES (?, ?,'
                      '?, ?, ?)',
                      (comment_id, post_id, message, created_time, int(time.time())))
            conn.commit()

    conn.close()


def get_all_posts(database_name, page_id, access_token):
    """
    Retrieve all posts for a given page and store them in the database.

    Parameters:
        page_id (str): The ID of the page to retrieve posts for.
        access_token (str): The access token to use for the Graph API.
        database_name (str): Path to the application db.

    Returns:
        None
    """

    graph = facebook.GraphAPI(access_token)

    posts = []
    page_posts = graph.get_object(page_id + '/posts')

    while True:
        for post in page_posts['data']:
            posts.append(post)

        if 'paging' in page_posts and 'next' in page_posts['paging']:
            page_posts = graph.get_connections(id=page_id, connection_name='posts',
                                               after=page_posts['paging']['cursors']['after'])
        else:
            break

    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    for post in posts:
        post_id = post['id']
        message = post.get('message', '')
        created_time = post['created_time']

        # Check if post already exists in the database
        c.execute('SELECT post_id FROM fb_posts WHERE post_id = ?', (post_id,))
        existing_post = c.fetchone()

        if existing_post is None:
            c.execute('INSERT INTO fb_posts (post_id, message, created_time, indexed_time) VALUES (?, ?, ?, ?)',
                      (post_id, message, created_time, int(time.time())))
            conn.commit()

    conn.close()


def get_all_post_comments(database_name, access_token):
    """
    Iterates through all posts and adds comments and store them in the database.

    Parameters:
        access_token (str): The access token to use for the Graph API.
        database_name (str): Path to the application db.

    Returns:
        None
    """

    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    c.execute('SELECT post_id FROM fb_posts')

    for row in c.fetchall():
        post_id = row[0]
        get_all_comments(database_name, post_id, access_token)

    conn.close()


def reply_to_comments(database_name, access_token):
    """
    Iterate through the comments table in the database and use Facebook API to reply to each comment with a completed
    status of 0. Once the comment has been successfully replied to, mark the completed column in the database with 1.

    Parameters:
        access_token (str): The access token to use for the Graph API.
        database_name (str): Path to the application db.

    Returns:
        None
    """

    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    c.execute('SELECT comment_id, message FROM comments WHERE completed = 0')
    openai.api_key = os.environ['OPEN_AI_API']
    graph = facebook.GraphAPI(access_token)

    for row in c.fetchall():
        comment_id, message = row[0], row[1]
        reply = "Hi! Thank you for commenting! If you mean to ask a question, make sure to put" \
                " [Question] before your comment. If you wanted to generate an AI DallE image, place [Image] before" \
                " your prompt!"

        if message.startswith('[Image]'):
            message = message[8:]  # remove the first 8 characters
            image = openai.Image.create(
                prompt=message,
                n=1,
                size="1024x1024"
            )

            if image:
                reply = image['data'][0]['url']

        if message.lowercase.startswith('[Question]'):
            message = message[11:]  # remove the first 11 characters
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": message}
                ]
            )

            if completion:
                reply = completion['choices'][0]['message']['content']

        if reply is not None:
            graph.put_comment(comment_id, 'DEV: {}'.format(reply))
            print('Reply to comment {}\nQ:{}\nA:{}'.format(comment_id, message, reply))
            c.execute('UPDATE comments SET completed = 1 WHERE comment_id = ?', (comment_id,))
            conn.commit()

    conn.close()


def post_to_facebook(database_name, access_token, table):
    """
    Post content from database tables. This can be used to pull random meme, or quote data to attach to facebook
    message.

        Parameters:
            access_token (str): The access token to use for the Graph API.
            table (str): The table name to retrieve post data.
            database_name (str): Path to the application db.

        Returns:
            None
        """

    graph = facebook.GraphAPI(access_token)
    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    c.execute(f'SELECT * FROM {table} WHERE posted = 0 ORDER BY RANDOM() LIMIT 1')
    row = c.fetchall()

    if 'memes' in table:
        if graph is not None:
            image_url = row[0][6]
            if not image_url.startswith('http'):
                image_url = 'http://' + image_url

            image_data = requests.get(image_url).content
            if "r/ProgrammerHumor" in row[0][1]:
                message = "{}\n#ProgrammerHumor \n#CodeLife \n#ProgrammingMemes \n#GeekHumor \n#TechLaughs \n#ITJokes " \
                          "\n#DebuggingLife \n#NerdLaughs \n#CodeJokes \n#SoftwareHumor \n#DevLife " \
                          "\n#ProgrammingProblems \n#HackerHumor \n#ByteJokes \n#MemeCode \n#LaughingCode " \
                          "\n#ProgrammingLaughs \n#CodeMemes \n#TechHumor \n#ComputingLaughs".format(row[0][2])
            else:
                message = "{}\n#RelatableMemes \n#FunnyMemes \n#MemeLife \n#HilariousMemes \n#MemeHumor " \
                          "\n#MemeJunkie \n#MemeAddict \n#MemeOfTheDay \n#SillyMemes \n#MemeVibes " \
                          "\n#DailyLaughs \n#HumorousMemes \n#MemeTime \n#MemeCentral " \
                          "\n#MemeCulture \n#MemeWar \n#MemeWorld \n#funnymemes \n#memesdaily " \
                          "\n#humor \n#funnyaf \n#memesarelife \n#memeoftheday \n#rofl " \
                          "\n#sillymemes \n#memeaddict \n#comedygold \n#memesfordays " \
                          "\n#haha \n#dailymemes".format(row[0][2])
            album_id = 'me/photos'
            graph.put_photo(image=image_data, album_id=album_id, message=message)
            update_table_post_status(database_name, table, row)
    elif 'quotes' in table:
        if graph is not None:
            message = f"{row[0][1]} - {row[0][0]}\n#lifequotes\n#inspirationalquotes\n#motivationalquotes\n" \
                      f"#quotestoliveby\n#positivequotes\n#wisdomquotes\n#mindfulnessquotes\n#gratitudequotes\n" \
                      f"#selflovequotes\n#spiritualquotes\n#meditationquotes\n#lovequotes\n#innerpeacequotes\n" \
                      f"#growthquotes\n#happinessquotes\n#successquotes\n#positivityquotes\n#mindsetquotes\n" \
                      f"#mindfulquotes\n#blessedquotes"
            graph.put_object('me', 'feed', message=message)
            update_table_post_status(database_name, table, row)


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

    conn = sqlite3.connect(database_name)
    c = conn.cursor()
    if 'memes' in table:
        c.execute(f'UPDATE {table} SET posted = 1, postedOn = {int(time.time())} WHERE id = ?', (row[0][0],))
        print(f'Updated {row[0][0]} to posted 1')
    elif 'quotes' in table:
        c.execute(f'UPDATE {table} SET posted = 1, postedOn = {int(time.time())} WHERE quote = ?', (row[0][1],))
        print(f'Updated {row[0][1]} to posted 1')

    conn.commit()
    conn.close()


def remove_dev_posts(page_id, access_token, regex_pattern):
    """
            This can be used to remove bulk posts on the requested Facebook PageID

                Parameters:
                    page_id (str): The ID of the page to retrieve posts for.
                    access_token (str): The access token to use for the Graph API.
                    regex_pattern (str): The regex pattern used to find specific types of messages on a post
                Returns:
                    None
                """
    graph = facebook.GraphAPI(access_token)

    # Retrieve all posts from page
    posts = graph.get_connections(page_id, "feed")

    # Loop through all posts and remove those that start with "dev_" and wildcard
    while True:
        for post in posts['data'][:-1]:
            if 'message' in post and re.search(regex_pattern, post['message'], re.IGNORECASE):
                graph.delete_object(post['id'])
                print(f"Deleted post with ID: {post['id']}")

        # Check if there are more pages of posts
        if 'paging' in posts and 'next' in posts['paging']:
            # Get the next page of posts
            posts = requests.get(posts['paging']['next']).json()
        else:
            break
