import imghdr
import logging
import os
import sqlite3
import time
from datetime import datetime

import praw
import requests
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

# set up logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs', 'reddit.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# log the start time
logging.info('Script started at {}'.format(datetime.now()))

# connect to the Reddit API using environment variables
try:
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                         client_secret=REDDIT_CLIENT_SECRET,
                         user_agent=REDDIT_USER_AGENT)
    logging.info('Connected to Reddit API')
except Exception as e:
    logging.error('Error connecting to Reddit API: {}'.format(e))
    reddit = None

subreddit_names = ['meme', 'dankmemes', 'funny']

if reddit is not None:
    while True:

        # retrieve top posts of the day from each subreddit in the list
        for subreddit_name in subreddit_names:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                top_posts = subreddit.top(time_filter='day', limit=100)
                logging.info('Retrieved top posts from subreddit {}'.format(subreddit_name))

                # filter posts that meet requirements
                filtered_posts = []
                for post in top_posts:
                    if not post.over_18 and post.score >= 50 and time.time() - post.created_utc <= 86400:
                        # check if URL ends with a recognized image format
                        if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            try:
                                # download image file using requests
                                response = requests.get(post.url)
                                if imghdr.what(None, h=response.content) is not None:
                                    filtered_posts.append(post)
                                else:
                                    logging.warning('Could not detect image format for post {}'.format(post.id))
                            except Exception as e:
                                logging.warning('Could not download image for post {}: {}'.format(post.id, e))
                        else:
                            logging.warning('Post {} is not an image file'.format(post.id))
            except Exception as e:
                logging.error('Error retrieving top posts from subreddit {}: {}'.format(subreddit_name, e))

        # save post metadata into a local sqlite db
        try:
            conn = sqlite3.connect(os.environ['DATABASE_NAME'])
            c = conn.cursor()

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

            for post in filtered_posts:
                c.execute("INSERT OR IGNORE INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (
                              post.id, 'reddit.com{}'.format(post.permalink), post.title, post.author.name, post.ups,
                              post.created_utc,
                              post.url,
                              int(time.time()), 0))

            conn.commit()
            conn.close()
            logging.info('Saved post metadata to database')
        except Exception as e:
            logging.error('Error saving post metadata to database: {}'.format(e))

        # log the end time
        logging.info('Script finished at {}'.format(datetime.now()))
        time.sleep(1800)
