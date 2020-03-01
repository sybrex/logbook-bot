import requests
import json
from requests.exceptions import HTTPError
import settings


def get_latest_topics():
    url = settings.API_HOST + '/topics?format=json'
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


def search_topics(name):
    topics = [
        {'id': 1001, 'title': 'Winter', 'created': '2020-02-21T13:41:25.767454Z'},
        {'id': 1005, 'title': 'Holidays', 'created': '2020-02-20T14:14:04.122992Z'}
    ]
    return topics


def lookup_story(id):
    if id == 111:
        story = {
            'id': 3,
            'type': 1,
            'description': 'Super story',
            'topic': {
                'id': 1010,
                'title': 'Football match',
                'created': '2020-02-20T14:14:04.122992Z'
            },
            'user': {
                'id': 3,
                'name': 'Jane',
                'phone': '380937861234',
                'status': 1
            },
            'content': 'img.jpg',
            'created': '2020-02-20T15:57:15.865215Z'
        }
        return story


def get_topic_by_id(topics, id):
    return next((topic for topic in topics if topic['id'] == id), None)
