import os
import logging
import logbook
from configparser import RawConfigParser
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

env = RawConfigParser()
env.read(BASE_DIR + '/env.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Main states
SELECT_TOPIC, SEARCH_TOPIC, CREATE_TOPIC_INTRO, CREATE_TOPIC, EDIT_TOPIC = range(5)

# Stories states
SELECT_STORY_TYPE, EDIT_STORY, VIDEO_STORY, PHOTO_STORY, TEXT_STORY = range(6, 11)

# Constants
TOPIC_START_OVER, START_OVER = range(11, 13)

# Meta states
STOPPING, SHOWING = range(13, 15)

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Callbacks
CALLBACK_VIDEO = 'video'
CALLBACK_PHOTO = 'photo'
CALLBACK_TEXT = 'text'
CALLBACK_BACK = 'back'
CALLBACK_EDIT = 'edit'
CALLBACK_SEARCH = 'search'
CALLBACK_NEW = 'new'

# Commands
COMMAND_START = 'start'
COMMAND_EXIT = 'exit'


def start(update, context):
    logger.info('Starting')
    logger.info('Update: %s', update)

    topics = logbook.get_latest_topics()
    context.user_data['topics'] = topics
    buttons = []
    for topic in topics:
        buttons.append([InlineKeyboardButton(text=topic['title'], callback_data=topic['id'])])
    buttons.append([
        InlineKeyboardButton(text='Search', callback_data=CALLBACK_SEARCH),
        InlineKeyboardButton(text='New', callback_data=CALLBACK_NEW)
    ])

    reply_markup = InlineKeyboardMarkup(buttons)

    if context.user_data.get(START_OVER):
        text = 'Here we go again!'
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        text = 'Greetings'
        update.message.reply_text(text=text, reply_markup=reply_markup)

    context.user_data[START_OVER] = False

    return SELECT_TOPIC


def edit_topic(update, context):
    logger.info('Editing topic')
    logger.info('Update: %s', update)

    buttons = [
        [InlineKeyboardButton(text='Video', callback_data=CALLBACK_VIDEO),
         InlineKeyboardButton(text='Photo', callback_data=CALLBACK_PHOTO),
         InlineKeyboardButton(text='Text', callback_data=CALLBACK_TEXT),
         InlineKeyboardButton(text='Edit', callback_data=CALLBACK_EDIT),
         InlineKeyboardButton(text='Back', callback_data=CALLBACK_BACK)]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if context.user_data.get(TOPIC_START_OVER):
        topic_id = context.user_data.get('topic_id')
        topic = logbook.get_topic_by_id(context.user_data.get('topics'), topic_id)
        text = 'Got it!\n' + topic['title']
        update.message.reply_text(text=text, reply_markup=reply_markup)
    else:
        topic_id = int(update.callback_query.data)
        context.user_data['topic_id'] = topic_id
        topic = logbook.get_topic_by_id(context.user_data.get('topics'), topic_id)
        text = topic['title']
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    context.user_data[TOPIC_START_OVER] = False

    return SELECT_STORY_TYPE


def search_topic_intro(update, context):
    logger.info('Search topic')
    text = 'Type the topic name to search'
    update.callback_query.edit_message_text(text=text)
    return SEARCH_TOPIC


def search_topic(update, context):
    logger.info('Searching for topic')
    logger.info('Update: %s', update)
    topics = logbook.search_topics(update.message.text)
    context.user_data['topics'] = topics

    buttons = []
    for topic in topics:
        buttons.append([InlineKeyboardButton(text=topic['title'], callback_data=topic['id'])])
    buttons.append([
        InlineKeyboardButton(text='Search', callback_data=CALLBACK_SEARCH),
        InlineKeyboardButton(text='New', callback_data=CALLBACK_NEW)
    ])

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text='Search results', reply_markup=reply_markup)
    context.user_data[START_OVER] = False

    return SELECT_TOPIC


def create_topic_intro(update, context):
    logger.info('New topic')
    text = 'Okay, type the new topic name'
    update.callback_query.edit_message_text(text=text)
    return CREATE_TOPIC


def create_topic(update, context):
    logger.info('Saving new topic %s', update.message.text)
    return start(update, context)


def close_topic(update, context):
    logger.info('Closing topic')
    context.user_data[START_OVER] = True
    start(update, context)
    return END


def edit_topic_story(update, context):
    logger.info('Editing topic story')
    return EDIT_STORY


def video_story(update, context):
    logger.info('Video story')
    return END


def photo_story(update, context):
    logger.info('Photo story')
    return END


def text_story(update, context):
    logger.info('Saving text story: %s', update.message.text)
    context.user_data[TOPIC_START_OVER] = True
    return edit_topic(update, context)


def ask_for_story(update, context):
    logger.info('Asking for story')
    logger.info('Update: %s', update)
    if update.callback_query.data == CALLBACK_TEXT:
        text = 'Tell your story'
        update.callback_query.edit_message_text(text=text)
        return TEXT_STORY
    elif update.callback_query.data == CALLBACK_VIDEO:
        text = 'Attach video'
        update.callback_query.edit_message_text(text=text)
        return VIDEO_STORY
    elif update.callback_query.data == CALLBACK_PHOTO:
        text = 'Attach photo'
        update.callback_query.edit_message_text(text=text)
        return PHOTO_STORY


def search_story(update, context):
    logger.info('Search for story')
    return EDIT_STORY


def close_nested(update, context):
    update.message.reply_text('Okay, bye.')
    return STOPPING


def end(update, context):
    logger.info('Exit')
    return END


def error(update, context):
    logger.error('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(env['telegram']['token'], use_context=True)
    dp = updater.dispatcher

    # Edit topic stories conversation
    topic_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_topic, pattern='^\d+$')],
        states={
            SELECT_STORY_TYPE: [
                CallbackQueryHandler(ask_for_story, pattern=f'^{CALLBACK_TEXT}|{CALLBACK_PHOTO}|{CALLBACK_VIDEO}$'),
                CallbackQueryHandler(edit_topic_story, pattern=f'^{CALLBACK_EDIT}$'),
                CallbackQueryHandler(close_topic, pattern=f'^{CALLBACK_BACK}$')
            ],
            EDIT_STORY: [MessageHandler(Filters.text, search_story)],
            VIDEO_STORY: [MessageHandler(Filters.video, video_story)],
            PHOTO_STORY: [MessageHandler(Filters.photo, photo_story)],
            TEXT_STORY: [MessageHandler(Filters.text, text_story)]
        },
        fallbacks=[
            CommandHandler(COMMAND_EXIT, close_nested)
        ],
        map_to_parent={
            STOPPING: STOPPING,
            END: SELECT_TOPIC
        }
    )

    # Main conversation
    main_conv = ConversationHandler(
        entry_points=[CommandHandler(COMMAND_START, start)],
        states={
            SELECT_TOPIC: [
                topic_conv,
                CallbackQueryHandler(search_topic_intro, pattern=f'^{CALLBACK_SEARCH}$'),
                CallbackQueryHandler(create_topic_intro, pattern=f'^{CALLBACK_NEW}$')
            ],
            SEARCH_TOPIC: [MessageHandler(Filters.text, search_topic)],
            CREATE_TOPIC: [MessageHandler(Filters.text, create_topic)]
        },
        fallbacks=[CommandHandler(COMMAND_EXIT, end)]
    )

    main_conv.states[STOPPING] = main_conv.entry_points

    dp.add_handler(main_conv)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
