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

# Constants
START_OVER = 'start'
SELECT_TOPIC = 'select_topic'
SEARCH_TOPIC = 'search_topic'
NEW_TOPIC = 'new_topic'
TYPING_REPLY = 'reply'
END = ConversationHandler.END


def start(update, context):
    buttons = [[
        InlineKeyboardButton(text='Winter', callback_data='Winter'),
        InlineKeyboardButton(text='Spring', callback_data='Spring'),
        InlineKeyboardButton(text='Summer', callback_data=str(3)),
        InlineKeyboardButton(text='Autumn', callback_data=str(4)),
        InlineKeyboardButton(text='New', callback_data=str(5)),
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    text = 'Greetings'
    update.message.reply_text(text=text, reply_markup=keyboard)

    return SELECT_TOPIC


def select_topic(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Your {}? Yes, I would love to hear about that!'.format(text.lower()))
    return ConversationHandler.END


def search_topic(update, context):
    logger.warning('Search topic', update, context.error)
    return ConversationHandler.END


def new_topic(update, context):
    logger.warning('New topic', update, context.error)
    return ConversationHandler.END


def cancel(update, context):
    logger.warning('Cancel', update, context.error)
    return ConversationHandler.END


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(env['telegram']['token'], use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_TOPIC: [MessageHandler(Filters.regex('^(Winter|Spring|Summer|Autumn)$'), select_topic)],
            NEW_TOPIC: [MessageHandler(Filters.regex('^(New)$'), new_topic)],
            SEARCH_TOPIC: [MessageHandler(Filters.text, select_topic)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
