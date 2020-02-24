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

# Meta states
STOPPING, SHOWING = map(chr, range(8, 10))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END


def start(update, context):
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    keyboard = [
        [InlineKeyboardButton(text='Winter', callback_data='winter'),
         InlineKeyboardButton(text='Spring', callback_data='spring'),
         InlineKeyboardButton(text='Summer', callback_data='summer'),
         InlineKeyboardButton(text='Autumn', callback_data='autumn'),
         InlineKeyboardButton(text='Search', callback_data='search'),
         InlineKeyboardButton(text='New', callback_data='new')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Greetings',
        reply_markup=reply_markup
    )

    return SELECT_TOPIC


def start_over(update, context):
    query = update.callback_query

    bot = context.bot
    keyboard = [
        [InlineKeyboardButton(text='Winter', callback_data='winter'),
         InlineKeyboardButton(text='Spring', callback_data='spring'),
         InlineKeyboardButton(text='Summer', callback_data='summer'),
         InlineKeyboardButton(text='Autumn', callback_data='autumn'),
         InlineKeyboardButton(text='Search', callback_data='search'),
         InlineKeyboardButton(text='New', callback_data='new')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text='Here we go again',
        reply_markup=reply_markup
    )
    return SELECT_TOPIC


def edit_topic(update, context):
    logger.info('Editing topic')
    query = update.callback_query

    bot = context.bot
    keyboard = [
        [InlineKeyboardButton(text='Video', callback_data='video'),
         InlineKeyboardButton(text='Photo', callback_data='photo'),
         InlineKeyboardButton(text='Text', callback_data='text'),
         InlineKeyboardButton(text='Edit', callback_data='edit'),
         InlineKeyboardButton(text='Back', callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text='Editing topic',
        reply_markup=reply_markup
    )
    return EDIT_TOPIC


def search_topic_intro(update, context):
    logger.info('Search topic')
    text = 'Okay, type the topic name'
    update.callback_query.edit_message_text(text=text)
    return SEARCH_TOPIC


def search_topic(update, context):
    logger.info('Searching for topic topic %s', update.message.text)
    return start(update, context)


def new_topic(update, context):
    logger.info('New topic')
    text = 'Okay, type the topic name'
    update.callback_query.edit_message_text(text=text)
    return ADD_TOPIC


def video_story(update, context):
    logger.info('Video story')
    return SELECT_TOPIC


def photo_story(update, context):
    logger.info('Photo story')
    return SELECT_TOPIC


def text_story(update, context):
    logger.info('Text story')
    return SELECT_TOPIC


def exit_nested(update, context):
    update.message.reply_text('Okay, bye.')
    return STOPPING


def save_topic(update, context):
    logger.info('Saving new topic %s', update.message.text)
    start(update, context)
    return ADD_TOPIC_INTRO


def topic_saved(update, context):
    logger.info('Topic saved')
    return END


def end(update, context):
    logger.info('Exit')
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text='See you next time'
    )
    return ConversationHandler.END


def error(update, context):
    logger.info('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(env['telegram']['token'], use_context=True)
    dp = updater.dispatcher

    # Adding new topic conversation
    new_topic_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_topic, pattern='^new$')],
        states={
            ADD_TOPIC_INTRO: [CallbackQueryHandler(new_topic, pattern='^(?!' + str(END) + ').*$')],
            ADD_TOPIC: [MessageHandler(Filters.text, save_topic)],
        },
        fallbacks=[
            CallbackQueryHandler(topic_saved, pattern='^' + str(END) + '$'),
            CommandHandler('exit', exit_nested)
        ],
        map_to_parent={
            END: SELECT_TOPIC,
            STOPPING: STOPPING,
        }
    )

    # Main conversation
    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_TOPIC: [
                CallbackQueryHandler(edit_topic, pattern='^winter|spring|summer|autumn$'),
                CallbackQueryHandler(search_topic_intro, pattern='^search$'),
                new_topic_conv
            ],
            SEARCH_TOPIC: [
                MessageHandler(Filters.text, search_topic)
            ],
            EDIT_TOPIC: [
                CallbackQueryHandler(video_story, pattern='^video'),
                CallbackQueryHandler(photo_story, pattern='^photo'),
                CallbackQueryHandler(text_story, pattern='^text'),
                CallbackQueryHandler(start_over, pattern='^back'),
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
