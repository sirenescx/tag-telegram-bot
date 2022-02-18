#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import json
import os
import logging
from random import randint
from telegram.ext import Updater, CommandHandler
from datetime import date, datetime


PORT = int(os.environ.get('PORT', 5000))
TOKEN = os.environ['TOKEN']
CHAT_ID = os.environ['CHAT_ID']

API_ENDPOINT = 'https://dog.ceo/api/breeds/image/random'


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def set_contest_date(update, context):
    try:
        _, start_date_str, end_date_str = update.message.text.split()
        start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
        end_date = datetime.strptime(end_date_str, '%d-%m-%Y')
        context.bot_data['start_date'] = start_date.date()
        context.bot_data['end_date'] = end_date.date()
    except:
        update.message.reply_text('Что-то пошло не по плану ☹️')


def start(update, context):
    update.message.reply_text('Привет! Теперь вам точно придется отвечать на вопросы в контестах')


def help(update, context):
    information: str = 'Доступные команды:\n' \
                       '\nУстановка новых дат контеста (дата в формате XX-XX-XXXX): \n' \
                       '/set_contest_date <start_date> <end_date>' \
                       '\n\nУстановка списка людей, которые отвечают на вопросы (указывается ник в tg):\n' \
                       '/set_users <user_1> <user_2> ... <user_n>\n' \
                       '\nПоказать текущие настройки бота: /show_settings '

    update.message.reply_text(information)


def set_users(update, context):
    try:
        _, *users = update.message.text.split()
        context.bot_data['users'] = users
    except:
        update.message.reply_text('Что-то пошло не по плану ☹️')


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def show_settings(update, context):
    settings: str = ''
    if 'users' in context.bot_data:
        settings += 'users: ' + ', '.join(context.bot_data['users'])
    if 'start_date' in context.bot_data and 'end_date' in context.bot_data:
        settings += f'\ncurrent contest dates: {str(context.bot_data["start_date"])} — {str(context.bot_data["end_date"])}'
    if 'last_execution_date' in context.bot_data:
        settings += f'\nlast tag was on {context.bot_data["last_execution_date"]}'

    if settings == '':
        update.message.reply_text('Настройки не заданы️')
    else:
        update.message.reply_text(settings)


def clear_last_execution_date(update, context):
    try:
        context.bot_data.pop('last_execution_date', None)
    except:
        update.message.reply_text('Что-то пошло не по плану ☹️')


def callback(context):
    current_date = datetime.now()

    if 'last_execution_date' in context.bot_data and context.bot_data['last_execution_date'].date() == current_date.date():
        return

    if 'start_date' in context.bot_data and 'end_date' in context.bot_data and 'users' in context.bot_data:
        start_date = context.bot_data['start_date']
        end_date = context.bot_data['end_date']

        if start_date <= current_date.date() <= end_date:
            if current_date.time().hour > 12:
                users = context.bot_data['users']
                context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f'{users[randint(0, len(users) - 1)]} проверь есть ли вопросы в контесте и ответь на них, если они есть'
                )
                context.bot_data['last_execution_date'] = current_date


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    jq = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('set_contest_date', set_contest_date))
    dp.add_handler(CommandHandler('set_users', set_users))
    dp.add_handler(CommandHandler('show_settings', show_settings))
    dp.add_handler(CommandHandler('clear_last_execution_date', clear_last_execution_date))

    job_minute = jq.run_repeating(callback, interval=1*60*60, first=120)

    dp.add_error_handler(error)

    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    updater.bot.setWebhook('https://your-app-name.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()
