import os
import shutil
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
DOWNLOAD_FILES = os.getenv('DOWNLOAD_FILES')
print 'download files: %s' % bool(DOWNLOAD_FILES)

HISTORY_URL = 'https://slack.com/api/conversations.history'
CHANNEL_INFO_URL = 'https://slack.com/api/conversations.info'

# channel_info_payload = {
#     'token': SLACK_TOKEN,
#     'channel': CHANNEL_ID
# }

HEADERS = {
    'Authorization': 'Bearer %s' % SLACK_TOKEN,
}


def _download_file(dl_url, out_file_path):
    r = requests.get(dl_url, headers=HEADERS, stream=True)
    with open(out_file_path, 'wb') as out_file:
        shutil.copyfileobj(r.raw, out_file)


def download_file(file_data):
    file_id = file_data['id']
    file_name = file_data['name']
    print 'downloading file %s/%s' % (file_id, file_name)
    file_url = file_data['url_private']
    if not os.path.isdir('%s/files/%s' % (DIRECTORY_NAME, file_id)):
        os.makedirs('%s/files/%s' % (DIRECTORY_NAME, file_id))
    out_file_path = '%s/files/%s/%s' % (DIRECTORY_NAME, file_id, file_name)
    _download_file(file_url, out_file_path)


for channel_id in CHANNEL_IDS:
    print 'processing channel %s' % channel_id
    cursor = True
    loops = 0
    payload = {
        'token': SLACK_TOKEN,
        'channel': channel_id,
        'limit': 200,
    }
    if not os.path.isdir(DIRECTORY_NAME):
        os.makedirs(DIRECTORY_NAME)
    filename = '%s/%s_%d.txt' % (
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
                if message.get('file'):
                    if DOWNLOAD_FILES:
                        download_file(message['file'])
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
