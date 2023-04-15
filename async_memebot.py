import aiohttp
import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
import facebook

load_dotenv()

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'memebot.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

logging.info('Script started at {}'.format(datetime.now()))

DATABASE_NAME = os.getenv('DATABASE_NAME')


async def post_to_facebook(row):
    graph = facebook.GraphAPI(access_token=os.environ['FACEBOOK_ACCESS_TOKEN'], version='3.0')

    # count the number of unposted rows
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM posts WHERE posted = 0')
    unposted_count = c.fetchone()[0]

    if graph is not None:
        try:
            image_url = row[6]
            if not image_url.startswith('http'):
                image_url = 'http://' + image_url

            image_data = requests.get(image_url).content
            message = "{} upvotes, posted on {}\n{} - original link\n" \
                      "I have {} memes left! Come back in 30 minutes for the next one!" \
                      "".format(row[4], datetime.fromtimestamp(row[5]),
                                              row[1], (unposted_count - 1))
            album_id = '{}/photos'.format(os.environ['FACEBOOK_ALBUM_ID'])
            graph.put_photo(image=image_data, album_id=album_id, message=message)
            logging.info(f"Post succeeded: {row['id']}")
            return True
        except Exception as e:
            logging.error(f"Post failed: {row['id']}, Error: {str(e)}")
            return False


async def update_post_status(conn, row):
    c = conn.cursor()
    c.execute('UPDATE posts SET posted = 1 WHERE id = ?', (row['id'],))
    conn.commit()
    logging.info('Updated post status for id: {}'.format(row['id']))


async def check_and_update_posts():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.row_factory = sqlite3.Row

    c.execute('SELECT * FROM posts WHERE posted = 0 AND created_utc < ? ORDER BY created_utc DESC', (datetime.now() - timedelta(minutes=15),))
    rows = c.fetchall()

    async with aiohttp.ClientSession() as session:
        for row in rows:
            response = await session.get(row['image_link'])
            if response.status == 200:
                if await post_to_facebook(row):
                    await update_post_status(conn, row)
                    break # Stop processing after posting one meme
            else:
                logging.warning('Image not available for id: {}'.format(row['id']))

    conn.close()
    logging.info('Waiting for 30 minutes before the next check')
    await asyncio.sleep(1800) # Wait for 30 minutes before checking for the next unposted meme


async def main_loop_meme():
    while True:
        await check_and_update_posts()

if __name__ == '__main__':
    asyncio.run(main_loop_meme())