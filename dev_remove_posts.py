import os
import logging
import re
import time
import facebook

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
    access_token = os.environ.get("FACEBOOK_ACCESS_TOKEN")
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    graph = facebook.GraphAPI(access_token)

    # Retrieve all posts from page
    posts = graph.get_connections(page_id, "feed")

    # Loop through all posts and remove those that start with "dev_" and wildcard
    count = 0
    while True:
        for post in posts['data'][:-1]:
            if 'message' in post and re.search(r'FTCbot says:.*', post['message'], re.IGNORECASE):
                graph.delete_object(post['id'])
                count += 1
                print(f"Deleted post with ID: {post['id']}")

        # Check if there are more pages of posts
        if 'paging' in posts and 'next' in posts['paging']:
            # Get the next page of posts
            posts = graph.get_object(posts['paging']['next'][26:])
        else:
            break

        # Wait for 1 second between each post removal
        time.sleep(1)

    # Post message to page with count of removed posts
    message = f"dev_automation: I have removed {count} posts."
    graph.put_object(page_id, "feed", message=message)
    print(message)


remove_dev_posts()