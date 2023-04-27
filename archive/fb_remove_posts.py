import os
import logging
import re
import time
import fb_tools
import requests

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'dev_rm_post.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


def remove_dev_posts():
    # Load environment variables
    load_dotenv()

    # Initialize Graph API client
    access_token = os.environ.get("FACEBOOK_PAGE_TOKEN")
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    graph = fb_tools.GraphAPI(access_token)

    # Retrieve all posts from page
    posts = graph.get_connections(page_id, "feed")

    # Loop through all posts and remove those that start with "dev_" and wildcard
    while True:
        for post in posts['data'][:-1]:
            if 'message' in post and re.search(r'.* - .*', post['message'], re.IGNORECASE):
                graph.delete_object(post['id'])
                print(f"Deleted post with ID: {post['id']}")

        # Check if there are more pages of posts
        if 'paging' in posts and 'next' in posts['paging']:
            # Get the next page of posts
            posts = requests.get(posts['paging']['next']).json()
        else:
            break


remove_dev_posts()
