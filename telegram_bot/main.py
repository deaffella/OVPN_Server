from telegram import Update
from telegram.ext import filters, \
    MessageHandler,\
    ApplicationBuilder, \
    CommandHandler, \
    ContextTypes, \
    CallbackContext, \
    CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.constants import ParseMode

import os
from dotenv import dotenv_values
import requests
from datetime import datetime
import ipaddress

import json
from utils.pagination import OVPNUsersPaginator


_secrets = dotenv_values("token.env.secret")
TOKEN = _secrets['TOKEN']
AUTHORIZED_TG_USERS = [str(usr['id']) for usr in json.load(open('./tg_users.json', 'r')).values()]

API_URL = os.getenv('API_URL')
OVPN_SUBNET = open('/ovpn/openvpn.conf', 'r').readline().removeprefix('server ').split(' ')[0]

ovpn_users_paginator = OVPNUsersPaginator()


def is_tg_user_in_whitelist(tg_id: str or int) -> bool:
    return str(tg_id) in AUTHORIZED_TG_USERS



async def command_start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_name = user.username if user.username else user.first_name

    if not is_tg_user_in_whitelist(tg_id=user.id):
        print('asdasdas')
        await context.bot.send_message(text='❌ Ты не в списке авторизованных пользователей! ❌ ',
                                       parse_mode=ParseMode.HTML,
                                       chat_id=update.effective_chat.id)
    else:
        text_to_reply = f'Привет, <b>{user_name}!</b>\n\n<i>tg_id: </i><code>{user.id}</code>'
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('🌐 OVPN Пользователи', callback_data=f"{ovpn_users_paginator.prefix}:page=1")],
            [InlineKeyboardButton('✉️ Telegram Пользователи', callback_data=f"telegram")],
            [InlineKeyboardButton('🛈 Инфо', callback_data=f"info")]])
        if hasattr(update, 'callback_query') and update.callback_query is not None:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(text=text_to_reply, parse_mode=ParseMode.HTML)
            await query.edit_message_reply_markup(reply_markup=reply_markup)
        else:
            await context.bot.send_message(text=text_to_reply,
                                           parse_mode=ParseMode.HTML,
                                           chat_id=update.effective_chat.id,
                                           reply_markup=reply_markup)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def check_ip(ip: str or int) -> bool:
        try:
            #ipaddress.ip_address(ip)
            _ip = int(ip)
            assert _ip > 1 and _ip < 255, Exception
            return True
        except:
            return False



    if not is_tg_user_in_whitelist(tg_id=update.message.from_user.id):
        await context.bot.send_message(text='❌ Ты не в списке авторизованных пользователей! ❌ ',
                                       parse_mode=ParseMode.HTML,
                                       chat_id=update.effective_chat.id)
    else:
        text_from_user = str(update.message.text)
        try:
            user_name, ip = text_from_user.removeprefix('ovpn-add ').split(' ')[:2]
            if not check_ip(ip):
                text_to_reply = f'❌ Невозможно добавить пользователя <code>{user_name}</code>!\n\nОшибка:\n<code>{"Некорректный IP!"}</code>'
            else:
                new_ip = '.'.join(OVPN_SUBNET.split('.')[:-1] + [str(int(ip))])
                result = requests.post(url=f'http://{API_URL}/add_user/', params={'name': user_name, 'ip': new_ip})
                if result.status_code == 200:
                    text_to_reply = f'✅ Пользователь <code>{user_name}</code> добавлен!'
                else:
                    result_data = result.json()
                    text_to_reply = f'❌ Невозможно добавить пользователя <code>{user_name}</code>!\n\nОшибка:\n<code>{result_data["detail"]}</code>'

            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=text_to_reply, parse_mode=ParseMode.HTML,
                                           reply_markup=InlineKeyboardMarkup([
                                               [InlineKeyboardButton('⬅️ Назад', callback_data=f"{ovpn_users_paginator.prefix}:page=1"),
                                                InlineKeyboardButton('🏠 Главное меню', callback_data=f"menu")]]))
        except:
            await show_all_ovpn_users(update=update, context=context)


async def show_all_ovpn_users(update: Update, context: CallbackContext):
    users_list = requests.get(url=f'http://{API_URL}/get_users/').json()
    text_to_reply = f"<b>🌐 OVPN Пользователи</b>\n\n" \
                    f"Всего пользователей: 🧑 <code>{len(users_list)}</code>\n" \
                    f"Текущая подсеть: 🌐 <code>{OVPN_SUBNET}</code>\n\n\n" \
                    f"<i>Для добавления и удаления пользователей отправь боту одну из следующих команд:</i>\n\n" \
                    f"✅ Добавить пользователя:\n<code>ovpn-add </code><b>USER_NAME   LAST_IP_OCTET</b>"
    if hasattr(update, 'callback_query') and update.callback_query is not None:
        query = update.callback_query
        selected_page = int(str(query.data).split('page=')[-1])
        await query.answer()
        await query.edit_message_text(text=text_to_reply, parse_mode=ParseMode.HTML)
        await query.edit_message_reply_markup(reply_markup=ovpn_users_paginator.get_keyboard(data_list=users_list,
                                                                                             page=selected_page))
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text_to_reply, parse_mode=ParseMode.HTML,
                                       reply_markup=ovpn_users_paginator.get_keyboard(data_list=users_list, page=1))


async def show_ovpn_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_name = query.data.split('name=')[-1]
    user_info = requests.get(url=f'http://{API_URL}/get_user_info/', params={'name': selected_name}).json()
    user_reg_date = datetime.strptime(user_info['created_at'], '%Y-%m-%dT%H:%M:%S.%f').strftime('🕓 <code>%H:%M:%S</code>\n🗓️ <code>%d.%m.%Y</code>')
    text_to_reply = f"🧑 Имя:\n<code>{user_info['name']}</code>\n\n" \
                    f"🖥️ IP:\n<code>{user_info['ip']}</code>\n\n" \
                    f"✍ Зарегистрирован:\n{user_reg_date}"
    await query.edit_message_text(text=text_to_reply, parse_mode=ParseMode.HTML)
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton('💾 Скачать сертификат', callback_data=f"{ovpn_users_paginator.prefix}:download={user_info['name']}")],
        [InlineKeyboardButton('❌ Удалить пользователя', callback_data=f"{ovpn_users_paginator.prefix}:delete={user_info['name']}")],
        [InlineKeyboardButton('⬅️ Назад', callback_data=f"{ovpn_users_paginator.prefix}:page=1"),
         InlineKeyboardButton('🏠 Главное меню', callback_data=f"menu")]]))


async def download_ovpn_certificate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_name = query.data.split('download=')[-1]
    user_info = requests.get(url=f'http://{API_URL}/get_user_info/', params={'name': selected_name}).json()
    certificate_file_name = str(user_info['certificate']).removeprefix('/etc/openvpn/ccd/')
    certificate_path = f"/ovpn/ccd/{certificate_file_name}"
    await update.effective_chat.send_document(open(certificate_path, 'rb'), caption='certificate_file_name')


async def delete_ovpn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_name = query.data.split('delete=')[-1]
    result = requests.delete(url=f'http://{API_URL}/delete_user/', params={'name': selected_name})
    result_data = result.json()
    if result.status_code == 200:
        text_to_reply = f'✅ Пользователь <code>{selected_name}</code> удален!'
    else:
        text_to_reply = f'❌ Невозможно удалить пользователя <code>{selected_name}</code>!\n\nОшибка:\n<code>{result_data["detail"]}</code>'
    await query.edit_message_text(text=text_to_reply, parse_mode=ParseMode.HTML)
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton('⬅️ Назад', callback_data=f"{ovpn_users_paginator.prefix}:page=1"),
         InlineKeyboardButton('🏠 Главное меню', callback_data=f"menu")]]))





if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', command_start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))

    application.add_handler(CallbackQueryHandler(command_start, pattern=f'^menu$'))
    application.add_handler(CallbackQueryHandler(show_all_ovpn_users, pattern=f'^{ovpn_users_paginator.prefix}:page=.*$'))
    application.add_handler(CallbackQueryHandler(show_ovpn_user_info, pattern=f'^{ovpn_users_paginator.prefix}:name=.*$'))
    application.add_handler(CallbackQueryHandler(download_ovpn_certificate, pattern=f'^{ovpn_users_paginator.prefix}:download=.*$'))
    application.add_handler(CallbackQueryHandler(delete_ovpn_user, pattern=f'^{ovpn_users_paginator.prefix}:delete=.*$'))

    application.run_polling()
