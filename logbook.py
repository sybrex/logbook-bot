import requests
import json
from requests.exceptions import HTTPError
import settings


def create_user(user):
    url = f'{settings.API_HOST}/users/?format=json'
    try:
        response = requests.post(url, data=user)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text)
        return {'status': True, 'data': data}


def get_telegram_user(id):
    url = f'{settings.API_HOST}/users?search={id}&format=json'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text)
        if len(data) == 0:
            return {'status': False}
        else:
            return {'status': True, 'data': data[0]}


def get_latest_topics():
    url = f'{settings.API_HOST}/topics?format=json'
    return api(url)


def search_topics(title):
    url = f'{settings.API_HOST}/topics?search={title}&format=json'
    return api(url)


def get_topic_stories(topic_id):
    url = f'{settings.API_HOST}/stories/?topic={topic_id}&format=json'
    return api(url)


def lookup_story(id):
    url = f'{settings.API_HOST}/stories/{id}?format=json'
    return api(url)


def remove_story(id):
    url = f'{settings.API_HOST}/stories/{id}/?format=json'
    try:
        response = requests.delete(url)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        return {'status': True}


def update_story(id, data):
    url = f'{settings.API_HOST}/stories/{id}/?format=json'
    try:
        response = requests.put(url, data=data)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text)
        return {'status': True, 'data': data}


def create_topic(title):
    url = f'{settings.API_HOST}/topics/?format=json'
    try:
        response = requests.post(url, data={'title': title})
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text)
        return {'status': True, 'data': data}


def create_story(story):
    url = f'{settings.API_HOST}/stories/?format=json'
    try:
        response = requests.post(url, data=story)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text)
        return {'status': True, 'data': data}


def api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        return {'status': False, 'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'status': False, 'error': f'API error occurred: {err}'}
    else:
        data = json.loads(response.text)
        return {'status': True, 'data': data}


def get_topic_by_id(topics, id):
    return next((topic for topic in topics if topic['id'] == id), None)
