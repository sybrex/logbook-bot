import logging
import logbook
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
import settings

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Main states
SELECT_TOPIC, SEARCH_TOPIC, CREATE_TOPIC_INTRO, CREATE_TOPIC, EDIT_TOPIC, LOOKUP_STORY = range(6)

# Stories states
SELECT_STORY_TYPE, EDIT_STORY, VIDEO_STORY, PHOTO_STORY, TEXT_STORY, UPDATE_STORY = range(7, 13)

# Constants
TOPIC_START_OVER, START_OVER = range(14, 16)

# Meta states
STOPPING, SHOWING = range(16, 18)

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
CALLBACK_LOOKUP = 'lookup'
CALLBACK_REMOVE = 'remove'

# Commands
COMMAND_START = 'start'
COMMAND_EXIT = 'exit'


def start(update, context):
    logger.info('Starting')
    logger.info('Update: %s', update)

    buttons = []
    topics = logbook.get_latest_topics()
    if topics['status']:
        context.user_data['topics'] = topics['data']
        for topic in topics['data']:
            buttons.append([InlineKeyboardButton(text=topic['title'], callback_data=topic['id'])])
    buttons.append([
        InlineKeyboardButton(text='Search Topic', callback_data=CALLBACK_SEARCH),
        InlineKeyboardButton(text='New Topic', callback_data=CALLBACK_NEW),
        InlineKeyboardButton(text='Lookup Story', callback_data=CALLBACK_LOOKUP)
    ])

    reply_markup = InlineKeyboardMarkup(buttons)
    text = context.user_data.pop('flash', 'Latest topics')

    if context.user_data.get(START_OVER):
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
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

    buttons = []
    topics = logbook.search_topics(update.message.text)
    if topics['status']:
        context.user_data['topics'] = topics['data']
        for topic in topics['data']:
            buttons.append([InlineKeyboardButton(text=topic['title'], callback_data=topic['id'])])
    buttons.append([
        InlineKeyboardButton(text='Search Topic', callback_data=CALLBACK_SEARCH),
        InlineKeyboardButton(text='New Topic', callback_data=CALLBACK_NEW),
        InlineKeyboardButton(text='Lookup Story', callback_data=CALLBACK_LOOKUP)
    ])

    reply_markup = InlineKeyboardMarkup(buttons)
    text = 'Search results' if topics['status'] and len(topics['data']) > 0 else 'Nothing found, try again'
    update.message.reply_text(text=text, reply_markup=reply_markup)
    context.user_data[START_OVER] = False

    return SELECT_TOPIC


def create_topic_intro(update, context):
    logger.info('New topic')
    text = 'Okay, type the new topic name'
    update.callback_query.edit_message_text(text=text)
    return CREATE_TOPIC


def lookup_story_intro(update, context):
    logger.info('Lookup story')
    text = 'Input story ID'
    update.callback_query.edit_message_text(text=text)
    return LOOKUP_STORY


def create_topic(update, context):
    logger.info('Saving new topic %s', update.message.text)
    topic = logbook.create_topic(update.message.text)
    if topic['status']:
        context.user_data['flash'] = 'New topic was created'
    else:
        context.user_data['flash'] = topic['error']
    return start(update, context)


def edit_story_intro(update, context):
    logger.info('Edit story description')
    text = 'Input story description'
    update.callback_query.edit_message_text(text=text)
    return UPDATE_STORY


def lookup_story(update, context):
    logger.info('Lookup story ID: %s', update.message.text)
    logger.info('Update: %s', update)
    story_id = int(update.message.text)
    context.user_data['story_id'] = story_id
    story = logbook.lookup_story(story_id)

    if story:
        text = story['description']
        buttons = [[
            InlineKeyboardButton(text='Remove', callback_data=CALLBACK_REMOVE),
            InlineKeyboardButton(text='Edit', callback_data=CALLBACK_EDIT),
            InlineKeyboardButton(text='Back', callback_data=CALLBACK_BACK)
        ]]
    else:
        text = f'Story {story_id} was not found'
        buttons = [[
            InlineKeyboardButton(text='Lookup again', callback_data=CALLBACK_LOOKUP),
            InlineKeyboardButton(text='Back', callback_data=CALLBACK_BACK)
        ]]

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text=text, reply_markup=reply_markup)

    return EDIT_STORY


def update_story(update, context):
    logger.info('Update story', update.message.text)
    logger.info('Update: %s', update)

    # TODO: update story description
    story_id = context.user_data.get('story_id')
    story_description = update.message.text

    text = story_description
    buttons = [[
        InlineKeyboardButton(text='Remove', callback_data=CALLBACK_REMOVE),
        InlineKeyboardButton(text='Edit', callback_data=CALLBACK_EDIT),
        InlineKeyboardButton(text='Back', callback_data=CALLBACK_BACK)
    ]]

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text=text, reply_markup=reply_markup)

    return EDIT_STORY


def remove_story(update, context):
    logger.info('Remove story')
    # TODO: Remove the story
    story_id = context.user_data.pop('story_id', None)
    context.user_data['flash'] = f'Story #{story_id} was removed'
    return close_story(update, context)


def close_topic(update, context):
    logger.info('Closing topic')
    context.user_data[START_OVER] = True
    start(update, context)
    return END


def video_story(update, context):
    logger.info('Video story')
    context.user_data[TOPIC_START_OVER] = True
    return edit_topic(update, context)


def photo_story(update, context):
    logger.info('Photo story')
    context.user_data[TOPIC_START_OVER] = True
    return edit_topic(update, context)


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


def close_story(update, context):
    logger.info('Closing story')
    context.user_data[START_OVER] = True
    return start(update, context)


def close_nested(update, context):
    update.message.reply_text('Okay, bye.')
    return STOPPING


def end(update, context):
    logger.info('Exit')
    return END


def error(update, context):
    logger.error('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(settings.TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Edit topic stories conversation
    topic_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_topic, pattern='^\d+$')],
        states={
            SELECT_STORY_TYPE: [
                CallbackQueryHandler(ask_for_story, pattern=f'^{CALLBACK_TEXT}|{CALLBACK_PHOTO}|{CALLBACK_VIDEO}$'),
                CallbackQueryHandler(close_topic, pattern=f'^{CALLBACK_BACK}$')
            ],
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
                CallbackQueryHandler(create_topic_intro, pattern=f'^{CALLBACK_NEW}$'),
                CallbackQueryHandler(lookup_story_intro, pattern=f'^{CALLBACK_LOOKUP}$'),
            ],
            EDIT_STORY: [
                CallbackQueryHandler(lookup_story_intro, pattern=f'^{CALLBACK_LOOKUP}$'),
                CallbackQueryHandler(edit_story_intro, pattern=f'^{CALLBACK_EDIT}$'),
                CallbackQueryHandler(remove_story, pattern=f'^{CALLBACK_REMOVE}$'),
                CallbackQueryHandler(close_story, pattern=f'^{CALLBACK_BACK}$')
            ],
            SEARCH_TOPIC: [MessageHandler(Filters.text, search_topic)],
            CREATE_TOPIC: [MessageHandler(Filters.text, create_topic)],
            LOOKUP_STORY: [MessageHandler(Filters.text, lookup_story)],
            UPDATE_STORY: [MessageHandler(Filters.text, update_story)],
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
