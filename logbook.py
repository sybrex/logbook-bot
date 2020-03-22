import requests
import json
from requests.exceptions import HTTPError
import settings


GET = 'get'
POST = 'post'
PUT = 'put'
DELETE = 'delete'


def get_telegram_user(id):
    url = f'{settings.API_HOST}/users?search={id}&format=json'
    user = api(GET, url)
    if user['status']:
        if len(user['data']) == 0:
            user['status'] = False
        else:
            user['data'] = user['data'][0]
    return user


def get_latest_topics():
    url = f'{settings.API_HOST}/topics?format=json'
    return api(GET, url)


def search_topics(title):
    url = f'{settings.API_HOST}/topics?search={title}&format=json'
    return api(GET, url)


def get_topic_stories(topic_id):
    url = f'{settings.API_HOST}/stories/?topic={topic_id}&format=json'
    return api(GET, url)


def lookup_story(id):
    url = f'{settings.API_HOST}/stories/{id}?format=json'
    return api(GET, url)


def create_user(user):
    url = f'{settings.API_HOST}/users/?format=json'
    return api(POST, url, user)


def remove_story(id):
    url = f'{settings.API_HOST}/stories/{id}/?format=json'
    return api(DELETE, url)


def remove_topic(id):
    url = f'{settings.API_HOST}/topics/{id}/?format=json'
    return api(DELETE, url)


def update_story(id, data):
    url = f'{settings.API_HOST}/stories/{id}/?format=json'
    return api(PUT, url, data)


def create_topic(title):
    url = f'{settings.API_HOST}/topics/?format=json'
    return api(POST, url, {'title': title})


def create_story(story):
    url = f'{settings.API_HOST}/stories/?format=json'
    return api(POST, url, story)


def api(method, url, data=None):
    headers = {'Authorization': 'Token ' + settings.API_TOKEN}
    try:
        if method == POST:
            response = requests.post(url, data=data, headers=headers)
        elif method == PUT:
            response = requests.put(url, data=data, headers=headers)
        elif method == DELETE:
            response = requests.delete(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text) if response.text else None
        return {'status': True, 'data': data}


def get_topic_by_id(topics, id):
    return next((topic for topic in topics if topic['id'] == id), None)


def get_topic_stories_count(topic_id):
    stories = get_topic_stories(topic_id)
    count = 0
    if stories['status']:
        count = len(stories['data'])
    return count