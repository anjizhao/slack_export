import os
import time

import arrow
from dotenv import find_dotenv, load_dotenv
import requests
import ujson

load_dotenv(find_dotenv())


SLACK_TOKEN = os.getenv('SLACK_TOKEN')
CHANNEL_IDS_STRING = os.getenv('CHANNEL_IDS')
CHANNEL_IDS = CHANNEL_IDS_STRING.split(',')
DIRECTORY_NAME = os.getenv('DIRECTORY_NAME') or '.'


HISTORY_URL = 'https://slack.com/api/conversations.history'
CHANNEL_INFO_URL = 'https://slack.com/api/conversations.info'

# channel_info_payload = {
#     'token': SLACK_TOKEN,
#     'channel': CHANNEL_ID
# }


for channel_id in CHANNEL_IDS:
    print 'processing channel %s' % channel_id
    cursor = True
    loops = 0
    payload = {
        'token': SLACK_TOKEN,
        'channel': channel_id,
        'limit': 200,
    }
    filename = '%s/conversation_%s_%d.txt' % (
        DIRECTORY_NAME, channel_id, arrow.utcnow().timestamp)
    with open(filename, 'w') as openfile:
        while cursor:
            response = requests.get(HISTORY_URL, payload)
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
