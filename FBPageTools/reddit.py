import sqlite3
import time
from dblogging import log_to_database
import imghdr
import os
import sqlite3
import time
import asyncpraw
import aiohttp

async def process_subreddit(database_name,subreddit_name,reddit_user_agent,reddit_client_id,reddit_client_secret):
    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    async with asyncpraw.Reddit(user_agent=reddit_user_agent,
                                client_id=reddit_client_id,
                                client_secret=reddit_client_secret) as reddit:
        try:
            subreddit = await reddit.subreddit(subreddit_name)
            top_posts = subreddit.top('day', limit=100)
            log_to_database(c, "INFO", f"Retrieved top posts from subreddit {subreddit_name}", "process_subreddit")

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
                                        log_to_database(c, "WARNING", f"Could not detect image format for post {post.id}", "process_subreddit")
                        except Exception as e:
                            log_to_database(c, "WARNING", f"Could not download image for post {post.id}: {e}", "process_subreddit")
                    else:
                        log_to_database(c, "WARNING", f"Post {post.id} is not an image file", "process_subreddit")
        except Exception as e:
            log_to_database(c, "ERROR", f"Error retrieving top posts from subreddit {subreddit_name}: {e}", "process_subreddit")
            filtered_posts = []

        # save post metadata into a local sqlite db
        try:
            for post in filtered_posts:
                c.execute("INSERT OR IGNORE INTO memes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (
                              post.id, 'reddit.com{}'.format(post.permalink), post.title, post.author.name, post.ups,
                              post.created_utc,
                              post.url,
                              int(time.time()), 0))

            conn.commit()
            log_to_database(c, "INFO", f"Saved post metadata to database for subreddit {subreddit_name}", "process_subreddit")
        except Exception as e:
            log_to_database(c, "ERROR", f"Error saving post metadata to database for subreddit {subreddit_name}: {e}", "process_subreddit")

    conn.close()