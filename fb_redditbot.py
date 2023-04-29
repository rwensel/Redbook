import asyncio
import imghdr
import logging
import os
import sqlite3
import time
from datetime import datetime

import asyncpraw
import aiohttp


async def process_subreddit(subreddit_name,reddit_user_agent,reddit_client_id,reddit_client_secret):

    async with asyncpraw.Reddit(user_agent=reddit_user_agent,
                                client_id=reddit_client_id,
                                client_secret=reddit_client_secret) as reddit:
        try:
            subreddit = await reddit.subreddit(subreddit_name)
            top_posts = subreddit.top('day', limit=100)

            # filter posts that meet requirements
            filtered_posts = []
            async for post in top_posts:
                if not post.over_18 and post.score >= 100 and time.time() - post.created_utc <= 86400:
                    # check if URL ends with a recognized image format
                    if post.url.endswith(('.jpg', '.jpeg', '.png')):
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(post.url) as response:
                                    if imghdr.what(None, h=await response.read()) is not None:
                                        filtered_posts.append(post)
                                    else:
                                        logging.warning('Could not detect image format for post {}'.format(post.id))
                    else:
                        logging.warning('Post {} is not an image file'.format(post.id))
        except Exception as e:
            filtered_posts = []

        # save post metadata into a local sqlite db

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



async def main_loop_reddit():
    subreddit_names = ['meme', 'me_irl', 'funny', 'ProgrammerHumor', 'starterpacks']
    while True:
        tasks = [process_subreddit(subreddit_name) for subreddit_name in subreddit_names]
        await asyncio.gather(*tasks)
        logging.info('Script finished at {}'.format(datetime.now()))
        time.sleep(21600)


if __name__ == '__main__':
    asyncio.run(main_loop_reddit())

