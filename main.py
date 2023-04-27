import os

from fb_tools import tools as fb
from rdt_tools import tools as rdt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

fb.OPEN_AI_API = os.getenv('')
fb.DATABASE_NAME = os.getenv('')
fb.FACEBOOK_PAGE_ID = os.getenv('')
fb.FACEBOOK_ACCESS_TOKEN = os.getenv('')
rdt.REDDIT_USER_AGENT = os.getenv('')
rdt.REDDIT_CLIENT_SECRET = os.getenv('')
rdt.REDDIT_CLIENT_ID = os.getenv('')

subreddit_names = ['meme', 'me_irl', 'funny', 'ProgrammerHumor', 'starterpacks']