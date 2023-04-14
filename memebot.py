import logging
import os
import sqlite3
import time
from datetime import datetime
import requests
import facebook
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

# set up logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'memebot.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# set up Facebook connection
try:
    graph = facebook.GraphAPI(access_token=os.environ['FACEBOOK_ACCESS_TOKEN'], version='3.0')
    page_id = os.environ['FACEBOOK_PAGE_ID']
    page_info = graph.get_object(id=page_id, fields='name')
    logging.info('Connected to Facebook page "{}"'.format(page_info['name']))
except Exception as e:
    logging.error('Error connecting to Facebook page: {}'.format(e))
    graph = None
    page_id = None

if graph is not None:
    # make a test post
    test_post_successful = False
    while not test_post_successful:
        try:
            test_message = 'This is a test post'
            graph.put_object(parent_object=page_id, connection_name='feed', message=test_message)
            logging.info('Made test post to Facebook page')

            # remove the test post
            posts = graph.get_connections(id=page_id, connection_name='feed')
            test_post = None
            for post in posts['data']:
                if post['message'] == test_message:
                    test_post = post
                    break
            if test_post is not None:
                graph.delete_object(id=test_post['id'])
                logging.info('Removed test post from Facebook page')
                test_post_successful = True
            else:
                logging.warning('Test post not found on Facebook page')
                test_post_successful = False
        except Exception as e:
            logging.error('Error making or removing test post from Facebook page: {}'.format(e))
            time.sleep(60)

    # enter the loop for posting random rows
    while test_post_successful:

        # connect to the database
        conn = sqlite3.connect(os.environ['DATABASE_NAME'])
        c = conn.cursor()

        # select a random unposted row of data from the database
        c.execute('SELECT * FROM posts WHERE posted = 0 ORDER BY RANDOM() LIMIT 1')
        row = c.fetchone()

        # post the data to Facebook
        if row is not None:
            try:
                # download image from URL
                image_url = row[7]
                if not image_url.startswith('http'):
                    image_url = 'http://' + image_url
                image_data = requests.get(image_url).content

                # create post message with image attachment
                message = '{} by {} - {} upvotes, {} downvotes\nposted on {}\nFTCMemeBot says:  See you in ' \
                          'an hour for the next meme! BleepBloopBlop'.format(row[2], row[3], row[4], row[5],
                                                                             datetime.fromtimestamp(row[6]))
                # upload image to Facebook album
                album_id = '{}/photos'.format(os.environ['FACEBOOK_ALBUM_ID'])
                image_upload = graph.put_photo(image=image_data, album_id=album_id, message=message)
                logging.info('Posted to Facebook page: {}'.format(message))

                # mark the row as posted
                c.execute('UPDATE posts SET posted = 1 WHERE id = ?', (row[0],))
                conn.commit()
                logging.info('Marked post as "posted" in database')
            except Exception as e:
                logging.error('Error posting to Facebook page: {}'.format(e))
        else:
            logging.info('No unposted posts found in database')

        conn.close()

        # wait for an hour
        time.sleep(3600)
