import asyncio
import csv
import json
import logging
import os
import random
from datetime import datetime

from dotenv import load_dotenv
import facebook

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_TOKEN')

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'quotebot.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logging.info('Script started at {}'.format(datetime.now()))

graph = facebook.GraphAPI(access_token=FACEBOOK_ACCESS_TOKEN, version='3.0')


def get_random_quote(filename, selected_quotes):
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='|')
        quotes = list(reader)
        available_quotes = [q for q in quotes if q not in selected_quotes and 'quote' in q and 'author' in q]
        if not available_quotes:
            selected_quotes = []
            available_quotes = quotes
        quote = random.choice(available_quotes)
        selected_quotes.append(quote)
        return quote, selected_quotes


async def post_random_quote(filename, selected_quotes):
    quote, selected_quotes = get_random_quote(filename, selected_quotes)
    message = f"{quote['quote']} - {quote['author']}\n#lifequotes\n#inspirationalquotes\n#motivationalquotes\n#quotestoliveby\n#positivequotes\n#wisdomquotes\n#mindfulnessquotes\n#gratitudequotes\n#selflovequotes\n#spiritualquotes\n#meditationquotes\n#lovequotes\n#innerpeacequotes\n#growthquotes\n#happinessquotes\n#successquotes\n#positivityquotes\n#mindsetquotes\n#mindfulquotes\n#blessedquotes"
    graph.put_object(parent_object='me', connection_name='feed', message=message)
    return selected_quotes


async def main_loop_quote():
    selected_quotes = []
    csv_file = '.\\files\\quotes.csv'
    sq_file = '.\\files\\selected_quotes.txt'
    posting_interval_minutes = 360

    # Read selected quotes from file, if it exists
    if os.path.exists(sq_file):
        with open(sq_file, 'r') as f:
            selected_quotes = json.load(f)

    while True:
        selected_quotes = await post_random_quote(csv_file, selected_quotes)

        # Write selected quotes to file
        with open(sq_file, 'w') as f:
            json.dump(selected_quotes, f)

        logging.info(f"Next post in {posting_interval_minutes} minutes")
        await asyncio.sleep(posting_interval_minutes * 60)


if __name__ == '__main__':
    asyncio.run(main_loop_quote())
