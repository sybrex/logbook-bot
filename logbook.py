def get_latest_topics():
    topics = [
        {'id': 1001, 'title': 'Winter', 'created': '2020-02-21T13:41:25.767454Z'},
        {'id': 1002, 'title': 'Spring', 'created': '2020-02-20T14:14:04.122992Z'},
        {'id': 1003, 'title': 'Summer', 'created': '2020-02-20T14:13:56.480670Z'},
        {'id': 1004, 'title': 'Autumn', 'created': '2020-02-20T14:13:49.020187Z'}
    ]
    return topics


def search_topics(name):
    topics = [
        {'id': 1001, 'title': 'Winter', 'created': '2020-02-21T13:41:25.767454Z'},
        {'id': 1005, 'title': 'Holidays', 'created': '2020-02-20T14:14:04.122992Z'}
    ]
    return topics


def get_topic_by_id(topics, id):
    return next((topic for topic in topics if topic['id'] == id), None)
