import logging
import os
import sqlite3
import time

import facebook
import openai
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(filename='logs/app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

DATABASE_NAME = os.environ['DATABASE_NAME']
FACEBOOK_PAGE_TOKEN = os.environ['FACEBOOK_PAGE_TOKEN']
FACEBOOK_PAGE_ID = os.environ['FACEBOOK_PAGE_ID']


def create_tables():
    """
    Create tables for storing posts and comments if they don't already exist in the database.

    Parameters:
        None

    Returns:
        None
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        post_id TEXT PRIMARY KEY,
        message TEXT,
        created_time TEXT
    )
    ''')

    # TODO: add chatai comment and time replied column to the comments table

    c.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        comment_id TEXT PRIMARY KEY,
        post_id TEXT,
        message TEXT,
        created_time TEXT,
        gen_text TEXT,
        gen_time TEXT,
        completed INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

    logging.info('Tables created successfully.')


def get_all_comments(post_id, access_token):
    """
    Retrieve all comments for a given post and store them in the database.

    Parameters:
        post_id (str): The ID of the post to retrieve comments for.
        access_token (str): The access token to use for the Graph API.

    Returns:
        None
    """

    # TODO: find a way to process comments to replies

    graph = facebook.GraphAPI(access_token)

    comments = graph.get_object(post_id + '/comments')

    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    for comment in comments['data']:
        comment_id = comment['id']
        message = comment.get('message', '')
        created_time = comment['created_time']

        # Check if comment already exists in the database
        c.execute('SELECT comment_id FROM comments WHERE comment_id = ?', (comment_id,))
        existing_comment = c.fetchone()

        if existing_comment is None:
            c.execute('INSERT INTO comments (comment_id, post_id, message, created_time) VALUES (?, ?, ?, ?)',
                      (comment_id, post_id, message, created_time))
            conn.commit()
            logging.info(f'New comment {comment_id} retrieved and stored for post {post_id}.')
        else:
            logging.info(f'Comment {comment_id} already exists in the database for post {post_id}.')

    conn.close()

    logging.info(f'{len(comments["data"])} comments retrieved and stored for post {post_id}.')


def get_all_posts(page_id, access_token):
    """
    Retrieve all posts for a given page and store them in the database.

    Parameters:
        page_id (str): The ID of the page to retrieve posts for.
        access_token (str): The access token to use for the Graph API.

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

    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    for post in posts:
        post_id = post['id']
        message = post.get('message', '')
        created_time = post['created_time']

        # Check if post already exists in the database
        c.execute('SELECT post_id FROM posts WHERE post_id = ?', (post_id,))
        existing_post = c.fetchone()

        if existing_post is None:
            c.execute('INSERT INTO posts (post_id, message, created_time) VALUES (?, ?, ?)',
                      (post_id, message, created_time))
            conn.commit()
            logging.info(f'New post {post_id} retrieved and stored for page {page_id}.')
        else:
            logging.info(f'Post {post_id} already exists in the database for page {page_id}.')

    conn.close()

    logging.info(f'{len(posts)} posts retrieved and stored for page {page_id}.')


def get_all_post_comments(access_token):
    """
    Retrieve all comments for all posts in the database and store them in the database.

    Parameters:
        access_token (str): The access token to use for the Graph API.

    Returns:
        None
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute('SELECT post_id FROM posts WHERE post_id = "105617929174026_115983561465954"')

    for row in c.fetchall():
        post_id = row[0]
        try:
            get_all_comments(post_id, access_token)
        except Exception as e:
            logging.error(f"Error getting comments for post {post_id}: {e}")

    conn.close()

    logging.info('All comments retrieved and stored successfully.')


def reply_to_comments(access_token):
    """
    Iterate through the comments table in the database and use Facebook API to reply to each comment with a completed
    status of 0. Once the comment has been successfully replied to, mark the completed column in the database with 1.

    Parameters:
        access_token (str): The access token to use for the Graph API.

    Returns:
        None
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute('SELECT comment_id, message FROM comments WHERE completed = 0')
    openai.api_key = os.environ['OPEN_AI_API']
    graph = facebook.GraphAPI(access_token)

    for row in c.fetchall():
        comment_id, message = row[0], row[1]
        reply = "Hi! Thank you for commenting! If you mean to ask a question, make sure to put" \
                " [Question] before your comment. If you wanted to generate an AI DallE image, place [Image] before" \
                " your prompt!"

    # TODO: log the chatai executions
    # TODO: update or insert chatai message and time replied to comments table

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

# TODO: add the chatai message to the post database and the time replied

        if reply is not None:
            try:
                graph.put_comment(comment_id, 'DEV: {}'.format(reply))
                print('Reply to comment {}\nQ:{}\nA:{}'.format(comment_id, message, reply))
                c.execute('UPDATE comments SET completed = 1 WHERE comment_id = ?', (comment_id,))
                conn.commit()
                logging.info(f'Replied to comment {comment_id} with message: {message}.')
            except Exception as e:
                logging.error(f"Error replying to comment {comment_id}: {e}")

    conn.close()


if __name__ == '__main__':
    while True:
        # create_tables()
        # get_all_posts(page_id=FACEBOOK_PAGE_ID, access_token=FACEBOOK_PAGE_TOKEN)
        get_all_post_comments(access_token=FACEBOOK_PAGE_TOKEN)
        reply_to_comments(access_token=FACEBOOK_PAGE_TOKEN)
        time.sleep(60)


# TODO: Add a fix for when function retrieves new comments and there is a comment to a comment. It causes the database to error
