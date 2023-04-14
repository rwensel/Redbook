import logging
import os
import sqlite3
import time
from datetime import datetime
from pyfacebook import GraphAPI
import requests
import facebook
from dotenv import load_dotenv

load_dotenv()

# set up logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'graphtest.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
pyfb = GraphAPI(access_token=os.environ['FACEBOOK_ACCESS_TOKEN'])
pyfb
print('end')
