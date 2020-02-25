import os
import logging
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
SELECT_TOPIC, SEARCH_TOPIC, ADD_TOPIC_INTRO, ADD_TOPIC, EDIT_TOPIC = range(5)

# Stories states
SELECT_STORY_TYPE, EDIT_STORY, VIDEO_STORY, PHOTO_STORY, TEXT_STORY = range(6, 11)

# Constants
TOPIC_START_OVER, START_OVER = range(11, 13)

# Meta states
STOPPING, SHOWING = range(13, 15)

# Shortcut for ConversationHandler.END
END = ConversationHandler.END


def start(update, context):
    logger.info('Starting')
    logger.info('Update: %s', update)

    keyboard = [
        [InlineKeyboardButton(text='Winter', callback_data='winter'),
         InlineKeyboardButton(text='Spring', callback_data='spring'),
         InlineKeyboardButton(text='Summer', callback_data='summer'),
         InlineKeyboardButton(text='Autumn', callback_data='autumn'),
         InlineKeyboardButton(text='Search', callback_data='search'),
         InlineKeyboardButton(text='New', callback_data='new')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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

    keyboard = [
        [InlineKeyboardButton(text='Video', callback_data='video'),
         InlineKeyboardButton(text='Photo', callback_data='photo'),
         InlineKeyboardButton(text='Text', callback_data='text'),
         InlineKeyboardButton(text='Edit', callback_data='edit'),
         InlineKeyboardButton(text='Back', callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get(TOPIC_START_OVER):
        text = 'Got it! Story name. Please select a story type'
        update.message.reply_text(text=text, reply_markup=reply_markup)
    else:
        text = 'Story name. Please select a story type'
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    context.user_data[TOPIC_START_OVER] = False

    return SELECT_STORY_TYPE


def search_topic_intro(update, context):
    logger.info('Search topic')
    text = 'Okay, type the topic name to search'
    update.callback_query.edit_message_text(text=text)
    return SEARCH_TOPIC


def search_topic(update, context):
    logger.info('Searching for topic topic %s', update.message.text)
    return start(update, context)


def new_topic(update, context):
    logger.info('New topic')
    text = 'Okay, type the new topic name'
    update.callback_query.edit_message_text(text=text)
    return ADD_TOPIC


def close_topic(update, context):
    logger.info('Closing topic')
    context.user_data[START_OVER] = True
    start(update, context)
    return END


def save_topic(update, context):
    logger.info('Saving new topic %s', update.message.text)
    start(update, context)
    return ADD_TOPIC_INTRO


def topic_saved(update, context):
    logger.info('Topic saved')
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
    if update.callback_query.data == 'text':
        text = 'Input text of the story'
        update.callback_query.edit_message_text(text=text)
        return TEXT_STORY
    elif update.callback_query.data == 'video':
        return VIDEO_STORY
    elif update.callback_query.data == 'photo':
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
        entry_points=[CallbackQueryHandler(edit_topic, pattern='^winter|spring|summer|autumn$')],
        states={
            SELECT_STORY_TYPE: [
                CallbackQueryHandler(ask_for_story, pattern='^photo|text|video$'),
                CallbackQueryHandler(edit_topic_story, pattern='^edit$'),
                CallbackQueryHandler(close_topic, pattern='^back$')
            ],
            EDIT_STORY: [MessageHandler(Filters.text, search_story)],
            VIDEO_STORY: [MessageHandler(Filters.video, video_story)],
            PHOTO_STORY: [MessageHandler(Filters.photo, photo_story)],
            TEXT_STORY: [MessageHandler(Filters.text, text_story)]
        },
        fallbacks=[
            CommandHandler('exit', close_nested)
        ],
        map_to_parent={
            STOPPING: STOPPING,
            END: SELECT_TOPIC
        }
    )

    # Main conversation
    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_TOPIC: [
                topic_conv,
                CallbackQueryHandler(search_topic_intro, pattern='^search$'),
                CallbackQueryHandler(new_topic, pattern='^new$')
            ],
            SEARCH_TOPIC: [
                MessageHandler(Filters.text, search_topic)
            ]
        },
        fallbacks=[CommandHandler('exit', end)]
    )

    main_conv.states[STOPPING] = main_conv.entry_points

    dp.add_handler(main_conv)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
