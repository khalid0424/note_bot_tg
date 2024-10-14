import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
from datetime import datetime

TOKEN = '8111006035:AAG47ubX9PWryQ29um4MtkB3xO-b5jp02jI'  
bot = telebot.TeleBot(TOKEN)

DB_CONNECTION = {
    'dbname': 'dbnote',
    'user': 'postgres',
    'password': 'Khalid2004',
    'host': 'localhost',
}

def connect_db():
    return psycopg2.connect(**DB_CONNECTION)

def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        username VARCHAR(255),
        created_at TIMESTAMP
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255),
        content TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        user_id BIGINT,
        chat_id BIGINT
    )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Ҷадвалҳо бомуваффақият сохта шуданд.")

def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("Илова кардани ёддошт"))
    keyboard.add(KeyboardButton("Дидани ёддоштҳо"))
    return keyboard

def register_user(telegram_id, username):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (telegram_id, username, created_at) VALUES (%s, %s, %s) ON CONFLICT (telegram_id) DO NOTHING",
                (telegram_id, username, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def add_note(user_id, title, content, chat_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (title, content, created_at, updated_at, user_id, chat_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (title, content, datetime.now(), datetime.now(), user_id, chat_id))
    conn.commit()
    cur.close()
    conn.close()

def get_notes(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM notes WHERE user_id = %s", (user_id,))
    notes = cur.fetchall()
    cur.close()
    conn.close()
    return notes

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    register_user(user_id, username)
    bot.reply_to(message, "Хуш омадед! Шумо бомуваффақият ба қайд гирифта шудед.", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "Илова кардани ёддошт")
def add_note_command(message):
    bot.reply_to(message, "Лутфан, номи ёддоштро ворид кунед:")
    bot.register_next_step_handler(message, process_note_title)

def process_note_title(message):
    title = message.text
    bot.reply_to(message, "Акнун матни ёддоштро ворид кунед:")
    bot.register_next_step_handler(message, process_note_content, title)

def process_note_content(message, title):
    content = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id
    add_note(user_id, title, content, chat_id)
    bot.reply_to(message, "Ёддошт бомуваффақият илова карда шуд!", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "Дидани ёддоштҳо")
def view_notes(message):
    user_id = message.from_user.id  
    notes = get_notes(user_id) 
    if notes:
        keyboard = InlineKeyboardMarkup()
        for note in notes:
            keyboard.add(InlineKeyboardButton(note[1], callback_data=f"view_note_{note[0]}"))
        bot.reply_to(message, "Интихоб кунед ёддоштро, ки мехоҳед бубинед:", reply_markup=keyboard)
    else:
        bot.reply_to(message, "Шумо ҳоло ягон ёддошт надоред.", reply_markup=create_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_note_'))
def callback_view_note(call):
    note_id = call.data.split('_')[2]
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT title, content FROM notes WHERE id = %s", (note_id,))
    note = cur.fetchone()
    cur.close()
    conn.close()
    if note:
        bot.answer_callback_query(call.id, "Ёддошт пайдо шуд")
        bot.send_message(call.message.chat.id, f"Номи ёддошт: {note[0]}\n\nМатн: {note[1]}")
    else:
        bot.answer_callback_query(call.id, "Ёддошт ёфт нашуд")


if __name__ == '__main__':
    create_tables()
    bot.polling(none_stop=True)

