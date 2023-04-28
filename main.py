import asyncio
import os
from dotenv import load_dotenv
from FBPageTools.reddit import process_subreddit

# Load environment variables
load_dotenv()
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_TOKEN')
DATABASE_NAME = os.getenv('DATABASE_NAME')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
OPEN_AI_API = os.getenv('OPEN_AI_API')
MODEL_ENGINE = os.getenv('MODEL_ENGINE')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
SUBREDDIT_NAMES = ['meme', 'me_irl', 'funny', 'ProgrammerHumor', 'starterpacks']

if __name__ == '__main__':
    [process_subreddit(DATABASE_NAME, SUBREDDIT_NAMES, REDDIT_USER_AGENT, REDDIT_CLIENT_SECRET, REDDIT_CLIENT_ID) for
     subreddit_name in SUBREDDIT_NAMES]
    # fb.create_tables(DATABASE_NAME)
    # fb.post_to_facebook(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN, 'quotes')
    # fb.post_to_facebook(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN, 'memes')
    # fb.get_all_posts(DATABASE_NAME, FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN)
    # fb.get_all_post_comments(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN)
    # fb.reply_to_comments(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN, MODEL_ENGINE, OPEN_AI_API)
