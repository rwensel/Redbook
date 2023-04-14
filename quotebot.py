import csv
import json
import logging
import os
import random
import time

from dotenv import load_dotenv
from facebook import GraphAPI, GraphAPIError

# Load environment variables
load_dotenv()

# set up logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'quotebot.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Set up Facebook Graph API connection
graph = GraphAPI(os.getenv('FACEBOOK_ACCESS_TOKEN'))


# Define a function to post a message
def post_message(message):
    try:
        graph.put_object("me", "feed", message=message)
        logging.info(f"Post succeeded: {message}")
    except GraphAPIError as e:
        logging.error(f"Post failed: {message}, Error: {e.message}")


# Define a function to test the API access
def test_api_access():
    try:
        graph.get_object('me')
        logging.info("API access test succeeded.")
        return True
    except GraphAPIError as e:
        logging.error(f"API access test failed. Error: {e.message}")
        return False


# Define a function to create a test post and delete it
def test_post_and_delete():
    try:
        message = "This is a test post."
        graph.put_object("me", "feed", message=message)
        logging.info(f"Test post created: {message}")
        posts = graph.get_connections("me", "posts")
        if len(posts['data']) > 0:
            post_id = posts['data'][0]['id']
            graph.delete_object(post_id)
            logging.info(f"Test post deleted: {post_id}")
            return True
        else:
            logging.error("Test post not found.")
            return False
    except GraphAPIError as e:
        logging.error(f"Test post failed. Error: {e.message}")
        return False


# Define a function to read a CSV file and return a random row
def get_random_quote(filename, selected_quotes):
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='|')
        quotes = list(reader)
        available_quotes = [q for q in quotes if q not in selected_quotes and 'quote' in q and 'author' in q]
        if not available_quotes:
            # If all quotes have been selected, reset the list of selected quotes
            selected_quotes = []
            available_quotes = quotes
        quote = random.choice(available_quotes)
        selected_quotes.append(quote)
        return quote, selected_quotes


# Define a function to post a message with a random quote
def post_random_quote(selected_quotes):
    quote, selected_quotes = get_random_quote('.\\files\\quotes.csv', selected_quotes)
    if 'quote' in quote and 'author' in quote:
        message = f"{quote['quote']} - {quote['author']:}\n\nFTCQuoteBot says: See you in an hour for the next quote! BleepBloopBlop"
        try:
            graph.put_object("me", "feed", message=message)
            logging.info(f"Post succeeded: {message}")
        except GraphAPIError as e:
            logging.error(f"Post failed: {message}, Error: {e.message}")
    else:
        logging.warning('Invalid quote data')
    return selected_quotes


# Run the bot
while True:
    if test_api_access():
        if test_post_and_delete():
            logging.info("All tests passed. Bot is ready to run.")
            # Load the list of selected quotes from the previous runs
            selected_quotes = []
            try:
                with open('.\\files\\selected_quotes.txt', 'r') as f:
                    data = f.read()
                    if data:
                        selected_quotes = json.loads(data)
            except FileNotFoundError:
                pass
            except json.JSONDecodeError:
                logging.error('Failed to decode selected quotes data')

            # Call the function to post a random quote and update the list of selected quotes
            selected_quotes = post_random_quote(selected_quotes)

            # Save the updated list of selected quotes to a file
            with open('.\\files\\selected_quotes.txt', 'w') as f:
                f.write(json.dumps(selected_quotes))
    logging.info("Waiting for 60 minutes before next test.")
    time.sleep(3600)
