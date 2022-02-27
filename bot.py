#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import os
import logging
from random import randint
from telegram.ext import Updater, CommandHandler
from datetime import timedelta, datetime
import requests

PORT = int(os.environ.get('PORT', 5000))
TOKEN = os.environ['TOKEN']
CHAT_ID = os.environ['CHAT_ID']
OAUTH_TOKEN = os.environ['OAUTH_TOKEN']
# curl -X GET "https://api.contest.yandex.net/api/public/v2/contests/34981" -H "accept: application/json" -H "Authorization: OAuth AQAAAAA3_mxGAAewRVM3xnu9WkuNhir7t0YHD68"

API_ENDPOINT = 'https://dog.ceo/api/breeds/image/random'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def set_contest_id(update, context):
    try:
        _, contest_id = update.message.text.split()

        try:
            request = requests.get(
                f'https://api.contest.yandex.net/api/public/v2/contests/{contest_id}/',
                headers={"accept": "application/json", "Authorization": f"OAuth {OAUTH_TOKEN}"}
            ).json()
        except:
            update.message.reply_text('Контеста с таким id не существует, либо у вас нет к нему доступа')
        contest_duration: int = timedelta(seconds=request['duration'])
        contest_start_date: datetime = datetime.strptime(request['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        contest_end_date = contest_start_date + contest_duration

        if contest_end_date < datetime.now():
            update.message.reply_text('Вы пытаесь задать уже закончившийся контест️')
        else:
            context.bot_data['contest_id'] = contest_id
            context.bot_data['contest_end_date'] = contest_end_date
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
        context.bot_data['users'] = [users[0], users[1], users[2], users[1], users[2]]
    except:
        update.message.reply_text('Что-то пошло не по плану ☹️')


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def show_settings(update, context):
    settings: str = ''
    if 'users' in context.bot_data:
        settings += 'users: ' + ', '.join(set(context.bot_data['users']))
    if 'contest_id' in context.bot_data:
        settings += f'\ncurrent contest: https://admin.contest.yandex.ru/contests/{context.bot_data["contest_id"]}/'
    if 'last_execution_date' in context.bot_data:
        settings += f'\nlast execution date: {context.bot_data["last_execution_date"]}'

    if settings == '':
        update.message.reply_text('Настройки не заданы️')
    else:
        update.message.reply_text(settings)


def clear_last_execution_date(update, context):
    try:
        context.bot_data.pop('last_execution_date', None)
    except:
        update.message.reply_text('Что-то пошло не по плану ☹️')


def get_phrase_inflection_by_number(number: int):
    if number == 0:
        return f'нет непрочитанных сообщений'
    if number % 10 == 1 and number != 11:
        return f'{number} непрочитанное сообщение. На него стоит ответить.'
    if 2 <= number % 10 <= 4 and number not in [12, 13, 14]:
        return f'{number} непрочитанных сообщения. На них нужно ответить!'
    else:
        return f'{number} непрочитанных сообщений. Студенты требуют внимания!'


def check_messages(context):
    if 'contest_id' in context.bot_data and 'users' in context.bot_data:
        if context.bot_data['contest_end_date'] < datetime.now():
            context.bot_data['contest_end_date'] = None
            return

        contest_id = context.bot_data['contest_id']
        users = context.bot_data['users']

        request = requests.get(
            f'https://api.contest.yandex.net/api/public/v2/contests/{contest_id}/messages/',
            headers={"accept": "application/json", "Authorization": f"OAuth {OAUTH_TOKEN}"}
        ).json()

        messages_with_no_answer = 0

        for message in request["messages"]:
            if len(message['answers']) == 0:
                messages_with_no_answer += 1

        if messages_with_no_answer > 0:
            context.bot.send_message(
                chat_id=CHAT_ID,
                text=f'{users[randint(0, len(users) - 1)]}, в контесте {get_phrase_inflection_by_number(messages_with_no_answer)}\n'
                     f'https://contest.yandex.ru/admin/contest-messages?contestId={contest_id}'
            )

        context.bot_data['last_execution_date'] = datetime.now()


def get_status(update, context):
    if 'contest_id' in context.bot_data:
        contest_id = context.bot_data['contest_id']

        if context.bot_data['contest_end_date'] < datetime.now():
            context.bot_data['contest_end_date'] = None
            return

        request = requests.get(
            f'https://api.contest.yandex.net/api/public/v2/contests/{contest_id}/messages/',
            headers={"accept": "application/json", "Authorization": f"OAuth {OAUTH_TOKEN}"}
        ).json()

        messages_with_no_answer = 0

        for message in request["messages"]:
            if len(message['answers']) == 0:
                messages_with_no_answer += 1

        context.bot.send_message(
            chat_id=CHAT_ID,
            text=f'В контесте {get_phrase_inflection_by_number(messages_with_no_answer)}\n'
                 f'https://contest.yandex.ru/admin/contest-messages?contestId={contest_id}'
        )
    else:
        context.bot.send_message(chat_id=CHAT_ID, text='Сейчас не идет контест')


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    jq = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('set_contest_id', set_contest_id))
    dp.add_handler(CommandHandler('set_users', set_users))
    dp.add_handler(CommandHandler('show_settings', show_settings))
    dp.add_handler(CommandHandler('clear_last_execution_date', clear_last_execution_date))
    dp.add_handler(CommandHandler('get_status', get_status))

    job_minute = jq.run_repeating(check_messages, interval=12 * 60 * 60, first=30)

    dp.add_error_handler(error)

    # updater.start_polling()
    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    updater.bot.setWebhook('https://tag-telegram-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()
