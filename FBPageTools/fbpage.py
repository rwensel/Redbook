import re
import sqlite3
import time

import facebook
import openai
import requests

from database import update_table_post_status
from dblogging import log_to_database


# ============================
# Function: get_all_comments
# ============================
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
    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering get_all_comments function', 'get_all_comments')

    # Initialize the Facebook Graph API with the access token
    try:
        graph = facebook.GraphAPI(access_token)
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

    # Get comments for the post
    try:
        comments = graph.get_object(post_id + '/comments')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

    # Iterate through the comments and insert them into the database
    for comment in comments['data']:
        comment_id = comment['id']
        message = comment.get('message', '')
        created_time = comment['created_time']

        # Check if comment already exists in the database
        try:
            c.execute('SELECT comment_id FROM fb_comments WHERE comment_id = ? AND message = ?', (comment_id, message))
            existing_comment = c.fetchone()
        except Exception as e:

            # Add a log entry for errors
            log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

        # Insert comment into the database
        if existing_comment is None:
            try:
                c.execute(
                    'INSERT INTO fb_comments (comment_id, post_id, message, created_time, indexed_time) VALUES (?, ?,'
                    '?, ?, ?)',
                    (comment_id, post_id, message, created_time, int(time.time())))
                conn.commit()
            except Exception as e:

                # Add a log entry for errors
                log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

    # Close the connection
    try:
        conn.close()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting get_all_comments function', 'get_all_comments')


# ============================
# Function: get_all_posts
# ============================
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

    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering get_all_posts function', 'get_all_posts')

    # Initialize the Facebook Graph API with the access token
    try:
        graph = facebook.GraphAPI(access_token)
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_posts: {str(e)}', 'get_all_posts')

    # Get posts for the page
    posts = []
    try:
        page_posts = graph.get_object(page_id + '/posts')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_posts: {str(e)}', 'get_all_posts')

    while True:
        for post in page_posts['data']:
            posts.append(post)

        if 'paging' in page_posts and 'next' in page_posts['paging']:
            page_posts = graph.get_connections(id=page_id, connection_name='posts',
                                               after=page_posts['paging']['cursors']['after'])
        else:
            break

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_posts: {str(e)}', 'get_all_posts')

    # Iterate through the posts and insert them into the database
    for post in posts:
        post_id = post['id']
        message = post.get('message', '')
        created_time = post['created_time']

        # Check if post already exists in the database
        try:
            c.execute('SELECT post_id FROM fb_posts WHERE post_id = ?', (post_id,))
            existing_post = c.fetchone()
        except Exception as e:

            # Add a log entry for errors
            log_to_database(database_name, 'ERROR', f'Error in get_all_posts: {str(e)}', 'get_all_posts')

        # Insert post into the database
        if existing_post is None:
            try:
                c.execute('INSERT INTO fb_posts (post_id, message, created_time, indexed_time) VALUES (?, ?, ?, ?)',
                          (post_id, message, created_time, int(time.time())))
                conn.commit()
            except Exception as e:

                # Add a log entry for errors
                log_to_database(database_name, 'ERROR', f'Error in get_all_posts: {str(e)}', 'get_all_posts')

    # Close the connection
    try:
        conn.close()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_posts: {str(e)}', 'get_all_posts')

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting get_all_posts function', 'get_all_posts')


# ============================
# Function: get_all_post_comments
# ============================
def get_all_post_comments(database_name, access_token):
    """
    Iterates through all posts and adds comments and store them in the database.

    Parameters:
        access_token (str): The access token to use for the Graph API.
        database_name (str): Path to the application db.

    Returns:
        None
    """

    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering get_all_post_comments function', 'get_all_post_comments')

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_post_comments: {str(e)}', 'get_all_post_comments')

    # Get all post_ids from the fb_posts table
    try:
        c.execute('SELECT post_id FROM fb_posts')
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_post_comments: {str(e)}', 'get_all_post_comments')

    # Iterate through the post_ids and get all comments for each post
    for row in c.fetchall():
        post_id = row[0]
        try:
            get_all_comments(database_name, post_id, access_token)
        except Exception as e:

            # Add a log entry for errors
            log_to_database(database_name, 'ERROR', f'Error in get_all_comments: {str(e)}', 'get_all_comments')

    # Close the connection
    try:
        conn.close()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in get_all_post_comments: {str(e)}', 'get_all_post_comments')

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting get_all_post_comments function', 'get_all_post_comments')


# ============================
# Function: reply_to_comments
# ============================
def reply_to_comments(database_name, access_token, model, openai_api):
    """
    Iterate through the comments table in the database and use Facebook API to reply to each comment with a completed
    status of 0. Once the comment has been successfully replied to, mark the completed column in the database with 1.
    Parameters:
        access_token (str): The access token to use for the Graph API.
        database_name (str): Path to the application db.
        model (str): OpenAI chat completion model.
        openai_api (str): OpenAi API Key.
    Returns:
        None
    """

    # Log function entry
    log_to_database(database_name, 'DEBUG', 'Entering reply_to_comments function', 'reply_to_comments')

    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    c.execute('SELECT comment_id, message FROM fb_comments WHERE completed = 0 and (message LIKE \'[Question]%\' OR '
              'message LIKE \'[Image]%\')')
    openai.api_key = openai_api
    graph = facebook.GraphAPI(access_token)

    for row in c.fetchall():
        try:
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

            if message.startswith('[Question]'):
                message = message[11:]  # remove the first 11 characters
                completion = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": message}
                    ]
                )

                if completion:
                    reply = completion['choices'][0]['message']['content']

            if reply is not None:
                graph.put_comment(comment_id, 'DEV: {}'.format(reply))
                print('Reply to comment {}\nQ:{}\nA:{}'.format(comment_id, message, reply))
                c.execute(
                    f'UPDATE fb_comments SET completed = 1, postedOn = {int(time.time())} WHERE comment_id = ? and '
                    f'message = ?', (comment_id, row[1]))
                conn.commit()
        except Exception as e:
            log_to_database(database_name, 'ERROR', f'Error processing comment: {comment_id}, Error: {str(e)}',
                            'reply_to_comments')

    # Log function exit
    log_to_database(database_name, 'DEBUG', 'Exiting reply_to_comments function', 'reply_to_comments')

    conn.close()


# ============================
# Function: post_to_facebook
# ============================
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

    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering post_to_facebook function', 'post_to_facebook')

    # Initialize the Facebook Graph API with the access token
    try:
        graph = facebook.GraphAPI(access_token)
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in post_to_facebook: {str(e)}', 'post_to_facebook')

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in post_to_facebook: {str(e)}', 'post_to_facebook')

    # Retrieve a random quote from the specified table in the database
    try:
        c.execute(f'SELECT * FROM {table} WHERE posted = 0 ORDER BY RANDOM() LIMIT 1')
        row = c.fetchall()
    except Exception as e:

        # Add a log entry for errors
        log_to_database(database_name, 'ERROR', f'Error in post_to_facebook: {str(e)}', 'post_to_facebook')

    # Checks the request to determine if it's to post a meme, or quote
    # For meme requests it will check the originating subreddit to determine what hashtags to apply
    if 'memes' in table:
        if graph is not None:
            image_url = row[0][6]
            if not image_url.startswith('http'):
                image_url = 'http://' + image_url

            image_data = requests.get(image_url).content
            if "r/ProgrammerHumor" in row[0][1]:
                message = "{}\n#ProgrammerHumor \n#CodeLife \n#ProgrammingMemes \n#GeekHumor \n#TechLaughs " \
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

            # Post the meme to the Facebook page
            try:
                graph.put_photo(image=image_data, album_id=album_id, message=message)
            except Exception as e:

                # Add a log entry for errors
                log_to_database(database_name, 'ERROR', f'Error in post_to_facebook: {str(e)}', 'post_to_facebook')

            # Update the meme's status in the database
            try:
                update_table_post_status(database_name, table, row)
            except Exception as e:

                # Add a log entry for errors
                log_to_database(database_name, 'ERROR', f'Error in update_table_post_status: {str(e)}',
                                'update_table_post_status')
    elif 'quotes' in table:
        if graph is not None:
            message = f"{row[0][1]} - {row[0][0]}\n#lifequotes\n#inspirationalquotes\n#motivationalquotes\n" \
                      f"#quotestoliveby\n#positivequotes\n#wisdomquotes\n#mindfulnessquotes\n#gratitudequotes\n" \
                      f"#selflovequotes\n#spiritualquotes\n#meditationquotes\n#lovequotes\n#innerpeacequotes\n" \
                      f"#growthquotes\n#happinessquotes\n#successquotes\n#positivityquotes\n#mindsetquotes\n" \
                      f"#mindfulquotes\n#blessedquotes"

            # Post the quote to the Facebook page
            try:
                graph.put_object('me', 'feed', message=message)
            except Exception as e:

                # Add a log entry for errors
                log_to_database(database_name, 'ERROR', f'Error in post_to_facebook: {str(e)}', 'post_to_facebook')

            # Update the quote's status in the database
            try:
                update_table_post_status(database_name, table, row)
            except Exception as e:

                # Add a log entry for errors
                log_to_database(database_name, 'ERROR', f'Error in update_table_post_status: {str(e)}',
                                'update_table_post_status')

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting post_to_facebook function', 'post_to_facebook')


# ============================
# Function: remove_dev_posts
# ============================
def remove_dev_posts(database_name, page_id, access_token, regex_pattern):
    """
    This can be used to remove bulk posts on the requested Facebook PageID

    Parameters:
        database_name (str): Path to the application db.
        page_id (str): The ID of the page to retrieve posts for.
        access_token (str): The access token to use for the Graph API.
        regex_pattern (str): The regex pattern used to find specific types of messages on a post
    Returns:
        None
    """
    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering remove_dev_posts function', 'remove_dev_posts')

    # Initialize the Facebook Graph API with the access token
    graph = facebook.GraphAPI(access_token)

    # Retrieve all posts from page
    posts = graph.get_connections(page_id, "feed")

    # Continuously loop through the posts until no more pages are available
    while True:
        # Loop through each post in the current batch of posts
        for post in posts['data'][:-1]:

            # Check if the post contains a message and if the message matches the regex pattern
            if 'message' in post and re.search(regex_pattern, post['message'], re.IGNORECASE):
                # Delete the post from the page
                graph.delete_object(post['id'])
                log_to_database(database_name, 'INFO', f'Deleted post with ID: {post["id"]}', 'remove_dev_posts')

        # Check if there are more pages of posts
        if 'paging' in posts and 'next' in posts['paging']:

            # Retrieve the next page of posts
            posts = requests.get(posts['paging']['next']).json()
        else:

            # If no more pages are available, break the loop
            break

    # Add a log entry for function exit
    log_to_database(database_name, 'DEBUG', 'Exiting remove_dev_posts function', 'remove_dev_posts')
