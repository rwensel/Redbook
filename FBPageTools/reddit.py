import asyncio
import imghdr
import sqlite3
import time

import aiohttp
import asyncpraw

from .dblogging import log_to_database


async def process_subreddit(database_name, subreddit_name, reddit_user_agent, reddit_client_id, reddit_client_secret):
    """
        Check sub reddit for new posts and indexes them into a db if they meet filtered
        requirements.

        Parameters:
            database_name (str): Path to the application db.
            subreddit_name (str): Iterated subreddit name
            reddit_user_agent (str): UserAgent info to report back to reddit api.
            reddit_client_id (str): Reddit API application ID.
            reddit_client_secret (str): Reddit API Access Key
        Returns:
            None
        """

    # Add a log entry for function entry
    log_to_database(database_name, 'DEBUG', 'Entering process_subreddit function', 'process_subreddit')

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
                                        log_to_database(database_name, 'INFO', 'Could not detect image.',
                                                        'process_subreddit')
                        except Exception as e:
                            log_to_database(database_name, 'ERROR', f'Error in process_subreddit: {str(e)}',
                                            'process_subreddit')
                    else:
                        log_to_database(database_name, 'INFO', f'Post {post.id} is not an image file',
                                        'process_subreddit')
        except Exception as e:
            log_to_database(database_name, 'ERROR', f'Error in process_subreddit: {str(e)}', 'process_subreddit')
            filtered_posts = []

        # save post metadata into a local sqlite db

        conn = sqlite3.connect(database_name)
        c = conn.cursor()

        for post in filtered_posts:
            try:
                c.execute("INSERT OR IGNORE INTO memes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (
                              post.id,
                              'reddit.com{}'.format(post.permalink),
                              post.title,
                              post.author.name,
                              post.ups,
                              post.created_utc,
                              post.url,
                              int(time.time()),
                              0,
                              '')),


            except Exception as e:
                log_to_database(database_name, 'ERROR', f'Error in process_subreddit: {str(e)}', 'process_subreddit')

        conn.commit()
        conn.close()
        log_to_database(database_name, 'DEBUG', 'Exiting process_subreddit function', 'process_subreddit')


async def main_loop_reddit(database_name, reddit_user_agent, reddit_client_id, reddit_client_secret):
    """
           Iterates through subreddit list using process_subreddit.

           Parameters:
               database_name (str): Path to the application db.
               reddit_user_agent (str): UserAgent info to report back to reddit api.
               reddit_client_id (str): Reddit API application ID.
               reddit_client_secret (str): Reddit API Access Key
           Returns:
               None
           """

    # Place the subreddits in which you want to check for posts within this list
    subreddit_names = ['meme', 'me_irl', 'funny', 'ProgrammerHumor', 'starterpacks']

    while True:
        tasks = [
            process_subreddit(database_name, subreddit_name, reddit_user_agent, reddit_client_id, reddit_client_secret)
            for subreddit_name in subreddit_names]
        await asyncio.gather(*tasks)
        time.sleep(21600)
