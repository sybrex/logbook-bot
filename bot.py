import logging
import logbook
import gettext
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
import settings


# i18n
trans = gettext.translation('bot', './i18n', languages=[settings.LANG], fallback=True)
trans.install()

# logging
loggingLevel = logging.getLevelName(settings.LOGGING_LEVEL)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=loggingLevel)
logger = logging.getLogger(__name__)

# stories types
TYPE_PHOTO = 1
TYPE_ALBUM = 2
TYPE_VIDEO = 3
TYPE_TEXT = 4

# main states
REGISTER, SELECT_TOPIC, SEARCH_TOPIC, CREATE_TOPIC, EDIT_TOPIC, LOOKUP_STORY, STOPPING = map(chr, range(7))

# stories states
SELECT_STORY_TYPE, EDIT_STORY, VIDEO_STORY, PHOTO_STORY, TEXT_STORY, UPDATE_STORY = map(chr, range(8, 14))

# callbacks
(CALLBACK_VIDEO, CALLBACK_PHOTO, CALLBACK_TEXT, CALLBACK_BACK, CALLBACK_EDIT, CALLBACK_SEARCH, CALLBACK_NEW,
 CALLBACK_LOOKUP, CALLBACK_REMOVE_TOPIC, CALLBACK_REMOVE_STORY) = map(chr, range(14, 24))

# commands
COMMAND_START = 'start'
COMMAND_EXIT = 'exit'
COMMAND_HELP = 'help'

PHOTO_SIZE = 640


def start(update, context):
    logger.debug('Starting')

    if not context.user_data.get('user'):
        user = logbook.get_telegram_user(update.effective_user.id)
        if user['status']:
            context.user_data['user'] = user['data']
        else:
            return register_intro(update)

    buttons = []
    topics = logbook.get_latest_topics()
    if topics['status']:
        context.user_data['topics'] = topics['data']
        for topic in topics['data']:
            buttons.append([InlineKeyboardButton(text=topic['title'], callback_data=topic['id'])])
    buttons.append([
        InlineKeyboardButton(text=_('search-topic'), callback_data=CALLBACK_SEARCH),
        InlineKeyboardButton(text=_('new-topic'), callback_data=CALLBACK_NEW),
        InlineKeyboardButton(text=_('lookup-story'), callback_data=CALLBACK_LOOKUP)
    ])

    reply_markup = InlineKeyboardMarkup(buttons)
    text = context.user_data.pop('flash', _('latest-topics'))

    if context.user_data.get('start_over'):
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        update.message.reply_text(text=text, reply_markup=reply_markup)

    context.user_data['start_over'] = False

    return SELECT_TOPIC


def register_intro(update):
    logger.debug('Registration intro')

    text = _('registration') + '\n' + _('input-registration-code')
    update.message.reply_text(text=text)
    return REGISTER


def register(update, context):
    logger.debug('Registration')

    if update.message.text == settings.REGISTRATION_CODE:
        data = {
            'telegram_id': update.effective_user.id,
            'first_name': update.effective_user.first_name,
            'last_name': update.effective_user.last_name,
            'username': update.effective_user.username
        }
        result = logbook.create_user(data)
        if result['status']:
            context.user_data['user'] = result['data']
            return start(update, context)
        else:
            logger.error(f"Registration \n {result['error']}")
            return ConversationHandler.END
    else:
        text = _('wrong-registration-code')
        update.message.reply_text(text=text)
        return REGISTER


def edit_topic(update, context):
    logger.debug('Editing topic')

    if context.user_data.get('topic_start_over'):
        topic_id = context.user_data.get('topic_id')
        topic = logbook.get_topic_by_id(context.user_data.get('topics'), topic_id)
        stories_count = logbook.get_topic_stories_count(topic_id)
        buttons = [
            [InlineKeyboardButton(text=_('video'), callback_data=CALLBACK_VIDEO),
             InlineKeyboardButton(text=_('photo'), callback_data=CALLBACK_PHOTO),
             InlineKeyboardButton(text=_('text'), callback_data=CALLBACK_TEXT)],
            [InlineKeyboardButton(text=_('back'), callback_data=CALLBACK_BACK)]
        ]
        if stories_count == 0:
            buttons[1].append(InlineKeyboardButton(text=_('remove'), callback_data=CALLBACK_REMOVE_TOPIC))
        reply_markup = InlineKeyboardMarkup(buttons)
        text = _('topic-info {topic_title} {stories_count}').format(
            topic_title=topic['title'],
            stories_count=stories_count
        )
        flash = context.user_data.pop('flash')
        if flash:
            text = f'{flash}\n{text}'
        update.message.reply_text(text=text, reply_markup=reply_markup)
    else:
        topic_id = int(update.callback_query.data)
        context.user_data['topic_id'] = topic_id
        topic = logbook.get_topic_by_id(context.user_data.get('topics'), topic_id)
        stories_count = logbook.get_topic_stories_count(topic_id)
        buttons = [
            [InlineKeyboardButton(text=_('video'), callback_data=CALLBACK_VIDEO),
             InlineKeyboardButton(text=_('photo'), callback_data=CALLBACK_PHOTO),
             InlineKeyboardButton(text=_('text'), callback_data=CALLBACK_TEXT)],
            [InlineKeyboardButton(text=_('back'), callback_data=CALLBACK_BACK)]
        ]
        if stories_count == 0:
            buttons[1].append(InlineKeyboardButton(text=_('remove'), callback_data=CALLBACK_REMOVE_TOPIC))
        reply_markup = InlineKeyboardMarkup(buttons)
        text = _('topic-info {topic_title} {stories_count}').format(
            topic_title=topic['title'],
            stories_count=stories_count
        )
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    context.user_data['topic_start_over'] = False

    return SELECT_STORY_TYPE


def search_topic_intro(update, context):
    logger.debug('Search topic intro')

    text = _('type-topic-name-to-search')
    update.callback_query.edit_message_text(text=text)
    return SEARCH_TOPIC


def search_topic(update, context):
    logger.debug('Searching for topic')

    buttons = []
    topics = logbook.search_topics(update.message.text)
    if topics['status']:
        context.user_data['topics'] = topics['data']
        for topic in topics['data']:
            buttons.append([InlineKeyboardButton(text=topic['title'], callback_data=topic['id'])])
    buttons.append([
        InlineKeyboardButton(text=_('search-topic'), callback_data=CALLBACK_SEARCH),
        InlineKeyboardButton(text=_('new-topic'), callback_data=CALLBACK_NEW),
        InlineKeyboardButton(text=_('lookup-story'), callback_data=CALLBACK_LOOKUP)
    ])

    reply_markup = InlineKeyboardMarkup(buttons)
    text = _('search-results') if topics['status'] and len(topics['data']) > 0 else _('nothing-found')
    update.message.reply_text(text=text, reply_markup=reply_markup)
    context.user_data['start_over'] = False

    return SELECT_TOPIC


def create_topic_intro(update, context):
    logger.debug('New topic intro')

    text = _('type-new-topic-name')
    update.callback_query.edit_message_text(text=text)
    return CREATE_TOPIC


def lookup_story_intro(update, context):
    logger.debug('Lookup story intro')

    text = _('input-story-id')
    update.callback_query.edit_message_text(text=text)
    return LOOKUP_STORY


def create_topic(update, context):
    logger.debug('Create new topic')

    topic = logbook.create_topic(update.message.text)
    if topic['status']:
        context.user_data['flash'] = _('new-topic-created')
    else:
        context.user_data['flash'] = topic['error']
    return start(update, context)


def edit_story_intro(update, context):
    logger.debug('Edit story description intro')

    text = _('input-story-description')
    update.callback_query.edit_message_text(text=text)
    return UPDATE_STORY


def lookup_story(update, context):
    logger.debug('Lookup story')

    try:
        story_id = int(update.message.text)
        context.user_data['story_id'] = story_id
        story = logbook.lookup_story(story_id)
    except ValueError as err:
        story_id = update.message.text
        story = {
            'status': False,
            'error': _('invalid-story-id')
        }

    if story['status']:
        text = _('story-info {id} {description}').format(
            id=story['data']['id'],
            description=story['data']['description']
        )
        if story['data']['type'] == TYPE_TEXT:
            text = f"{text}\n{story['data']['content']}"
        elif story['data']['type'] == TYPE_PHOTO:
            text = f"{text}\n{settings.SITE}/media/images/{PHOTO_SIZE}_{story['data']['content']}"
        elif story['data']['type'] == TYPE_ALBUM:
            # TODO
            pass
        elif story['data']['type'] == TYPE_VIDEO:
            text = f"{text}\n{settings.SITE}/media/videos/{PHOTO_SIZE}_{story['data']['content']}"
            pass
        buttons = [[
            InlineKeyboardButton(text=_('remove'), callback_data=CALLBACK_REMOVE_STORY),
            InlineKeyboardButton(text=_('edit'), callback_data=CALLBACK_EDIT),
            InlineKeyboardButton(text=_('back'), callback_data=CALLBACK_BACK)
        ]]
    else:
        text = _('story-not-found {id}').format(id=story_id)
        logger.error(f"Lookup story {story['error']}")
        buttons = [[
            InlineKeyboardButton(text=_('lookup-again'), callback_data=CALLBACK_LOOKUP),
            InlineKeyboardButton(text=_('back'), callback_data=CALLBACK_BACK)
        ]]

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text=text, reply_markup=reply_markup)

    return EDIT_STORY


def update_story(update, context):
    logger.debug('Update story')

    story_id = context.user_data.get('story_id')
    story_description = update.message.text
    result = logbook.update_story(story_id, {'description': story_description})
    if result['status']:
        text = _('story-successfully-updated {id}').format(id=story_id)
    else:
        text = _('could-not-update-story {id}').format(id=story_id)
        logger.error(f"Update story {result['error']}")
    buttons = [[
        InlineKeyboardButton(text=_('remove'), callback_data=CALLBACK_REMOVE_STORY),
        InlineKeyboardButton(text=_('edit'), callback_data=CALLBACK_EDIT),
        InlineKeyboardButton(text=_('back'), callback_data=CALLBACK_BACK)
    ]]

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text=text, reply_markup=reply_markup)

    return EDIT_STORY


def remove_story(update, context):
    logger.debug('Remove story')

    story_id = context.user_data.pop('story_id', None)
    result = logbook.remove_story(story_id)
    if result['status']:
        context.user_data['flash'] = _('story-removed {id}').format(id=story_id)
    else:
        context.user_data['flash'] = _('could-not-remove-story {id}').format(id=story_id)
        logger.error(f"Remove story {result['error']}")
    return close_story(update, context)


def remove_topic(update, context):
    logger.debug('Remove topic')

    topic_id = context.user_data.pop('topic_id', None)
    result = logbook.remove_topic(topic_id)
    if result['status']:
        context.user_data['flash'] = _('topic-removed {id}').format(id=topic_id)
    else:
        context.user_data['flash'] = _('could-not-remove-topic {id}').format(id=topic_id)
        logger.error(f"Remove topic {result['error']}")
    return close_topic(update, context)


def close_topic(update, context):
    logger.debug('Closing topic')

    context.user_data['start_over'] = True
    start(update, context)
    return ConversationHandler.END


def video_story(update, context):
    logger.debug('Video story')

    video_file = update.message.video.get_file()
    data = {
        'type': TYPE_VIDEO,
        'description': update.message.caption,
        'topic': context.user_data['topic_id'],
        'user': context.user_data['user']['id'],
        'content': video_file.file_path
    }
    result = logbook.create_story(data)

    if result['status']:
        context.user_data['flash'] = _('story-created {id} {description}').format(
            id=result['data']['id'],
            description=result['data']['description']
        )
    else:
        logger.error(f"Text story create {result['error']}")

    context.user_data['topic_start_over'] = True
    return edit_topic(update, context)


def photo_story(update, context):
    logger.debug('Photo story')

    photo_file = update.message.photo[-1].get_file()
    data = {
        'type': TYPE_PHOTO,
        'description': update.message.caption,
        'topic': context.user_data['topic_id'],
        'user': context.user_data['user']['id'],
        'content': photo_file.file_path
    }
    result = logbook.create_story(data)

    if result['status']:
        context.user_data['flash'] = _('story-created {id} {description}').format(
            id=result['data']['id'],
            description=result['data']['description']
        )
    else:
        logger.error(f"Text story create {result['error']}")

    context.user_data['topic_start_over'] = True
    return edit_topic(update, context)


def text_story(update, context):
    logger.debug('Saving text story')

    data = {
        'type': TYPE_TEXT,
        'description': '',
        'topic': context.user_data['topic_id'],
        'user': context.user_data['user']['id'],
        'content': update.message.text
    }
    result = logbook.create_story(data)

    if result['status']:
        context.user_data['flash'] = _('story-created {id}').format(id=result['data']['id'])
    else:
        logger.error(f"Text story create {result['error']}")

    context.user_data['topic_start_over'] = True
    return edit_topic(update, context)


def ask_for_story(update, context):
    logger.debug('Asking for story')

    if update.callback_query.data == CALLBACK_TEXT:
        text = _('input-text-story')
        update.callback_query.edit_message_text(text=text)
        return TEXT_STORY
    elif update.callback_query.data == CALLBACK_VIDEO:
        text = _('input-video-story')
        update.callback_query.edit_message_text(text=text)
        return VIDEO_STORY
    elif update.callback_query.data == CALLBACK_PHOTO:
        text = _('input-photo-story')
        update.callback_query.edit_message_text(text=text)
        return PHOTO_STORY


def invalid_attachment(update, context):
    logger.debug('Invalid attachement')

    context.user_data['flash'] = _('invalid-attachment')
    context.user_data['topic_start_over'] = True
    return edit_topic(update, context)


def close_story(update, context):
    logger.debug('Closing story')

    context.user_data['start_over'] = True
    return start(update, context)


def close_nested(update, context):
    logger.debug('Close nested')

    update.message.reply_text(_('bye'))
    return STOPPING


def end(update, context):
    logger.debug('Exit')

    update.message.reply_text(_('bye'))
    return ConversationHandler.END


def help(update, context):
    logger.debug('Help')

    text = _('help {site}').format(site=settings.SITE)
    update.message.reply_text(text=text)
    return ConversationHandler.END


def nested_help(update, context):
    logger.debug('Close nested help')

    text = _('help {site}').format(site=settings.SITE)
    update.message.reply_text(text=text)
    return STOPPING


def error(update, context):
    logger.error(f'{context.error} with update \n{update}')


def main():
    updater = Updater(settings.TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Edit topic stories conversation
    topic_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_topic, pattern='^\d+$')],
        states={
            SELECT_STORY_TYPE: [
                CallbackQueryHandler(ask_for_story, pattern=f'^{CALLBACK_TEXT}|{CALLBACK_PHOTO}|{CALLBACK_VIDEO}$'),
                CallbackQueryHandler(remove_topic, pattern=f'^{CALLBACK_REMOVE_TOPIC}$'),
                CallbackQueryHandler(close_topic, pattern=f'^{CALLBACK_BACK}$')
            ],
            VIDEO_STORY: [
                MessageHandler(Filters.video, video_story),
                MessageHandler(Filters.photo, invalid_attachment),
                MessageHandler(Filters.document, invalid_attachment)
            ],
            PHOTO_STORY: [
                MessageHandler(Filters.photo, photo_story),
                MessageHandler(Filters.document, invalid_attachment)
            ],
            TEXT_STORY: [MessageHandler(Filters.text, text_story)]
        },
        fallbacks=[
            CommandHandler(COMMAND_EXIT, close_nested),
            CommandHandler(COMMAND_HELP, nested_help),
        ],
        map_to_parent={
            STOPPING: STOPPING,
            ConversationHandler.END: SELECT_TOPIC
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
                CallbackQueryHandler(remove_story, pattern=f'^{CALLBACK_REMOVE_STORY}$'),
                CallbackQueryHandler(close_story, pattern=f'^{CALLBACK_BACK}$')
            ],
            REGISTER: [MessageHandler(Filters.text, register)],
            SEARCH_TOPIC: [MessageHandler(Filters.text, search_topic)],
            CREATE_TOPIC: [MessageHandler(Filters.text, create_topic)],
            LOOKUP_STORY: [MessageHandler(Filters.text, lookup_story)],
            UPDATE_STORY: [MessageHandler(Filters.text, update_story)],
        },
        fallbacks=[
            CommandHandler(COMMAND_EXIT, end),
            CommandHandler(COMMAND_HELP, help)
        ]
    )

    main_conv.states[STOPPING] = main_conv.entry_points

    dp.add_handler(main_conv)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
