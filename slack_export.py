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
USER_INFO_URL = 'https://slack.com/api/users.info'

CHANNEL_DATA_KEYS = [
    'name_normalized', 'topic', 'id', 'purpose', 'name', 'user'
]

USER_DATA_KEYS = [
    'name', 'real_name', 'id', 'profile',
]

USER_PROFILE_KEYS = [
    'status_emoji', 'status_text', 'display_name', 'email',
]

FILE_KEYS_TO_POP = [
    'image_exif_rotation', 'display_as_bot', 'preview', 'preview_highlight',
    'external_type', 'is_external', 'public_url_shared', 'editable',
    'is_public',
]

HEADERS = {
    'Authorization': 'Bearer %s' % SLACK_TOKEN,
}


users = {}
channels = {}

def _download_file(dl_url, out_file_path):
    r = requests.get(dl_url, headers=HEADERS, stream=True)
    with open(out_file_path, 'wb') as out_file:
        shutil.copyfileobj(r.raw, out_file)


def download_file(file_data, channel_id):
    file_id = file_data['id']
    file_name = file_data['name']
    file_url = file_data['url_private']
    out_file_path = '%s/%s_files/%s/%s' % (
        DIRECTORY_NAME, channel_id, file_id, file_name)
    if os.path.exists(out_file_path):
        print 'file already exists: %s' % out_file_path
        return
    if not os.path.isdir('%s/%s_files/%s' % (
            DIRECTORY_NAME, channel_id, file_id)):
        os.makedirs('%s/%s_files/%s' % (
            DIRECTORY_NAME, channel_id, file_id))
    print 'downloading file to %s_files/%s/%s' % (
        channel_id, file_id, file_name)
    _download_file(file_url, out_file_path)


def get_channel_data(channel_id):
    payload = {
        'token': SLACK_TOKEN,
        'channel': channel_id,
    }
    r = requests.get(CHANNEL_INFO_URL, payload)
    if r.status_code != 200:
        print r.status_code, r.text
        raise Exception(r.status_code)
    return r.json().get('channel', {})


def clean_channel_data(channel_data):
    channel_data = {
        k: v for k, v in channel_data.iteritems() if k in CHANNEL_DATA_KEYS
    }
    if channel_data.get('user'):
        user = get_user(channel_data['user'])
        channel_data['user_name'] = (
            user.get('name') or user.get('real_name') or
            user.get('display_name'))
    return channel_data


def get_user_data(user_id):
    payload = {
        'token': SLACK_TOKEN,
        'user': user_id,
    }
    r = requests.get(USER_INFO_URL, payload)
    if r.status_code != 200:
        print r.status_code, r.text
        raise Exception(r.status_code)
    return r.json().get('user', {})


def clean_user_data(user_data):
    user_data = {
        k: v for k, v in user_data.iteritems() if k in USER_DATA_KEYS
    }
    for k, v in user_data.pop('profile', {}).iteritems():
        if k in USER_PROFILE_KEYS:
            user_data[k] = v
    return user_data


def get_user(user_id):
    if users.get(user_id):
        return users[user_id]
    else:
        user_data = get_user_data(user_id)
        user_data = clean_user_data(user_data)
        users[user_id] = user_data
        return user_data


def save_users_channels():
    # load users already written to file
    existing_users = {}
    user_filename = '%s/users.txt' % DIRECTORY_NAME
    if os.path.exists(user_filename):
        with open(user_filename, 'r') as openfile:
            lines = openfile.readlines()
            lines = [l.rstrip('\n') for l in lines]
            items = [ujson.loads(l) for l in lines]
            for i in items:
                existing_users[i['id']] = i

    # write (append) new users to file
    with open(user_filename, 'a') as openfile:
        for k, v in users.iteritems():
            if k not in existing_users:
                print 'saving user %s' % v['id']
                openfile.write(ujson.dumps(v) + '\n')

    # load channels already written to file
    existing_channels = {}
    channel_filename = '%s/channels.txt' % DIRECTORY_NAME
    if os.path.exists(channel_filename):
        with open(channel_filename, 'r') as openfile:
            lines = [l.rstrip('\n') for l in openfile.readlines()]
            items = [ujson.loads(l) for l in lines]
            for i in items:
                existing_channels[i['id']] = i

    # write (append) new channels to file
    with open(channel_filename, 'a') as openfile:
        for k, v in channels.iteritems():
            if k not in existing_channels:
                print 'saving channel %s' % v['id']
                openfile.write(ujson.dumps(v) + '\n')

    return


for channel_id in CHANNEL_IDS:
    print 'processing channel %s' % channel_id
    cursor = True
    loops = 0
    payload = {
        'token': SLACK_TOKEN,
        'channel': channel_id,
        'limit': 400,
    }
    if not os.path.isdir(DIRECTORY_NAME):
        os.makedirs(DIRECTORY_NAME)
    filename = '%s/%s_%d.txt' % (
        DIRECTORY_NAME, channel_id, arrow.utcnow().timestamp)
    # get channel info
    channel_data = get_channel_data(channel_id)
    channel_data = clean_channel_data(channel_data)
    channels[channel_id] = channel_data
    # get data
    with open(filename, 'w') as openfile:
        while cursor:
            response = requests.get(HISTORY_URL, payload)
            if response.status_code != 200:
                print response.status_code, response.text
                raise Exception(response.status_code)
            data = response.json()
            messages = data.get('messages') or []
            writestring = ''
            for message in messages:
                if message.get('file'):
                    if DOWNLOAD_FILES:
                        download_file(message['file'], channel_id)
                    for key in message['file'].keys():
                        if key in FILE_KEYS_TO_POP or 'thumb' in key:
                            message['file'].pop(key)
                if message.get('user'):
                    user = get_user(message['user'])
                    message['username'] = (
                        user.get('name') or user.get('real_name') or
                        user.get('display_name'))
                line = ujson.dumps(message)
                writestring += (line + '\n')
                if len(writestring) >= 10000:
                    openfile.write(writestring)
                    writestring = ''
            cursor = None
            if data.get('has_more'):
                if data.get('response_metadata'):
                    cursor = data.get('response_metadata').get('next_cursor')
                    payload['cursor'] = cursor
            loops += 1
            if loops % 20 == 0:
                print loops, message['ts']
            time.sleep(.5)
        save_users_channels()
