import os
from configparser import RawConfigParser


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

env = RawConfigParser()
env.read(BASE_DIR + '/env.ini')

TELEGRAM_TOKEN = env['telegram']['token']
API_HOST = env['api']['host']
API_TOKEN = env['api']['token']
REGISTRATION_CODE = env['telegram']['code']

LANG = env['settings']['language']
LOGGING_LEVEL = env['settings']['logging_level']
SITE = env['settings']['site']
