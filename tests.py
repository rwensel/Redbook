import os
from dotenv import load_dotenv
from FBPageTools import fbpage as fb
from FBPageTools import reddit as rddt
# Load environment variables
load_dotenv()
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_TOKEN')
DATABASE_NAME = os.getenv('DATABASE_NAME')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
OPEN_AI_API = os.getenv('OPEN_AI_API')
MODEL_ENGINE = os.getenv('MODEL_ENGINE')
REDDIT_CLIENT_ID= os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET= os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT= os.getenv('REDDIT_USER_AGENT')

subreddit_name=[]

rddt.process_subreddit(DATABASE_NAME,subreddit_name,REDDIT_USER_AGENT,REDDIT_CLIENT_ID,REDDIT_CLIENT_SECRET)
fb.create_tables(DATABASE_NAME)
fb.post_to_facebook(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN, 'quotes')
fb.post_to_facebook(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN, 'memes')
fb.get_all_posts(DATABASE_NAME, FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN)
fb.get_all_post_comments(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN)
fb.reply_to_comments(DATABASE_NAME, FACEBOOK_ACCESS_TOKEN, MODEL_ENGINE, OPEN_AI_API)
