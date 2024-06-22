import telebot
from telebot import types
import sqlite3
import threading
import time
from datetime import datetime
import schedule

bot = telebot.TeleBot('7407698133:AAFW2fKubPA7BGjpiuOuI6umeCmSQ_lpITM')


@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('my_database.sql')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS birthdays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_user VARCHAR(50),
        name VARCHAR(50),
        date VARCHAR(50),
        date_format VARCHAR(50)
        )
        ''')
    conn.commit()
    cur.close()
    conn.close()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('➕ Добавить ДР')
    btn2 = types.KeyboardButton('➖ Удалить ДР')
    btn3 = types.KeyboardButton('📋 Показать список всех ДР')
    keyboard.add(btn1, btn2)
    keyboard.add(btn3)
    bot.send_message(message.chat.id, 'Привет! Этот бот позволяет создавать напоминания о днях рождения.',
                     reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == '➕ Добавить ДР')
def instructions_add(message):
    bot.send_message(message.chat.id,
                     'Введите информацию о ДР.\nМожно ввести несколько ДР (каждый на отдельной строчке).\n\nПример:\n15 мая - Вася')
    bot.register_next_step_handler(message, add_birthday)


def add_birthday(message):
    conn = sqlite3.connect('my_database.sql')
    cur = conn.cursor()

    id_user = message.chat.id
    months = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06', 'июля': '07',
              'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12', }
    f = 0
    for line in message.text.split('\n'):
        data = [x.strip() for x in line.split('-')]
        name = data[1] if len(data)==2 else ''
        date = data[0].lower().split()

        if not (date[0].isdigit() and 1 <= int(date[0]) <= 31 and date[1] in months):
            f = 1
            continue
        day = date[0] if int(date[0]) > 9 else '0' + date[0]
        month = months[date[1]]
        date_format = f"2024-{month}-{day}"
        cur.execute('INSERT INTO birthdays (id_user, name, date, date_format) VALUES ("%s", "%s", "%s" , "%s")' % (
            id_user, name, data[0], date_format))

    conn.commit()
    cur.close()
    conn.close()
    if f == 0:
        bot.reply_to(message, 'Добавление выполнено успешно')
    else:
        bot.reply_to(message, 'Встречена некорректная дата. Повторите команду для этой записи.')


@bot.message_handler(func=lambda message: message.text == '📋 Показать список всех ДР')
def show_birthdays(message):
    conn = sqlite3.connect('my_database.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT name, date, date_format FROM birthdays WHERE id_user={message.chat.id} ORDER BY date_format')
    birthdays = cur.fetchall()
    cur.close()
    conn.close()
    if len(birthdays):
        info = ''
        for elem in birthdays:
            info += f'{elem[1]} - {elem[0]}\n'
        bot.send_message(message.chat.id, info)
    else:
        bot.send_message(message.chat.id, "Вы пока не добавили ни одной записи")


@bot.message_handler(func=lambda message: message.text == '➖ Удалить ДР')
def instructions_delete(message):
    conn = sqlite3.connect('my_database.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT id, name, date FROM birthdays WHERE id_user={message.chat.id} ORDER BY name')
    birthdays = cur.fetchall()
    cur.close()
    conn.close()
    if len(birthdays):
        ids_birthdays = [x[0] for x in birthdays]
        info = ''
        k = 0
        for elem in birthdays:
            k += 1
            info += f'{k}.  {elem[1]} - {elem[2]}\n'

        bot.send_message(message.chat.id,
                         f'Пришлите номер удаляемой записи (можно несколько - через запятую).\n\n{info}')
        bot.register_next_step_handler(message, delete_birthday, ids_birthdays)
    else:
        bot.send_message(message.chat.id, "Вы пока не добавили ни одной записи")


def delete_birthday(message, ids_birthdays):
    del_list = [ids_birthdays[int(i) - 1] for i in message.text.split(',') if 1<=int(i)<=len(ids_birthdays)]
    conn = sqlite3.connect('my_database.sql')
    cur = conn.cursor()
    f = 0
    for id_del in del_list:
        cur.execute(f'DELETE FROM birthdays WHERE id={id_del}')

    conn.commit()
    cur.close()
    conn.close()
    bot.reply_to(message, 'Удаление прошло успешно')


def reminders():
    conn = sqlite3.connect('my_database.sql')
    cur = conn.cursor()
    date = '2024-' + datetime.now().strftime('%m-%d')
    cur.execute('SELECT id_user, name FROM birthdays WHERE date_format="%s"' % date)
    birthdays = cur.fetchall()

    for elem in birthdays:
        bot.send_message(elem[0], f'Сегодня день рождения отмечает: {elem[1]}')

    cur.close()
    conn.close()


def scheduler():
    schedule.every().day.at("10:00").do(reminders)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    thread = threading.Thread(target=scheduler)
    thread.start()
    bot.polling(none_stop=True)
