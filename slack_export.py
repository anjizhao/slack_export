import os
import time

import arrow
from dotenv import find_dotenv, load_dotenv
import requests
import ujson

load_dotenv(find_dotenv())


SLACK_TOKEN = os.getenv('SLACK_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

URL = 'https://slack.com/api/conversations.history'

payload = {
    'token': SLACK_TOKEN,
    'channel': CHANNEL_ID,
    'limit': 200,
}

filename = 'slack_dump_%s_%d.txt' % (CHANNEL_ID, arrow.utcnow().timestamp)

cursor = True

loops = 0

with open(filename, 'w') as openfile:
    while cursor:
        response = requests.get(URL, payload)
        if response.status_code != 200:
            print response.status_code, response.text
            raise Exception(response.status_code)
        data = response.json()
        messages = data.get('messages') or []
        for message in messages:
            line = ujson.dumps(message)
            openfile.write(line + '\n')
        cursor = None
        if data.get('has_more'):
            if data.get('response_metadata'):
                cursor = data.get('response_metadata').get('next_cursor')
                payload['cursor'] = cursor
        loops += 1
        if loops % 20 == 0:
            print loops, message['ts']
        time.sleep(.5)
