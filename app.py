import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import threading

app = Flask(__name__)

BOT_TOKEN = "8905123015:AAE5PW-yGvvMlgLgHXicvlI9Qdz1tHBM0gs"
OWNER_ID = 5024310561
SITE_URL = "https://telegram-stats-viewer.netlify.app"
USERS_FILE = "/home/Schizo/users_data.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def send_message(chat_id, text, reply_markup=None):
    def _send():
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        try:
            requests.post(url, json=data, timeout=10)
        except:
            pass
    # Отправляем в отдельном потоке, чтобы не блокировать webhook
    threading.Thread(target=_send).start()

def answer_callback(callback_id):
    def _answer():
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
        data = {"callback_query_id": callback_id}
        try:
            requests.post(url, json=data, timeout=5)
        except:
            pass
    threading.Thread(target=_answer).start()

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update:
        return "ok", 200
    # Сообщения
    message = update.get('message')
    if message:
        chat_id = message['chat']['id']
        username = message['chat'].get('username', str(chat_id))
        text = message.get('text', '')
        users = load_users()
        if str(chat_id) not in users:
            users[str(chat_id)] = {
                "first_seen": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "username": username,
                "coins": 0
            }
            save_users(users)
        if text == '/start':
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📊 Статистика", "url": SITE_URL}],
                    [{"text": "👤 Профиль", "callback_data": "profile"}],
                    [{"text": "🎲 Игры", "callback_data": "games"}]
                ]
            }
            send_message(chat_id, "🔍 *Telegram Stats Checker*\nВыбери действие:", keyboard)
        elif text == '/send_stats' and chat_id == OWNER_ID:
            parts = text.split()
            if len(parts) == 2:
                target = parts[1]
                if target in users:
                    msg_cnt = random.randint(5000, 50000)
                    reg_year = random.randint(2015, 2024)
                    contacts = random.randint(20, 300)
                    stats = f"📊 *Ваша статистика*\n✉️ Сообщений: {msg_cnt}\n📅 Регистрация: {reg_year}\n👥 Контактов: {contacts}\n✅ Аккаунт в безопасности."
                    send_message(int(target), stats)
                    send_message(chat_id, f"✅ Статистика отправлена {target}")
                else:
                    send_message(chat_id, f"❌ Пользователь {target} не найден")
        else:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📊 Статистика", "url": SITE_URL}],
                    [{"text": "👤 Профиль", "callback_data": "profile"}],
                    [{"text": "🎲 Игры", "callback_data": "games"}]
                ]
            }
            send_message(chat_id, "Главное меню:", keyboard)
    # Callback-запросы
    elif 'callback_query' in update:
        cb = update['callback_query']
        chat_id = cb['message']['chat']['id']
        data = cb['data']
        answer_callback(cb['id'])  # асинхронно отвечаем
        if data == 'profile':
            users = load_users()
            u = users.get(str(chat_id), {})
            first = u.get('first_seen', 'неизвестно')
            coins = u.get('coins', 0)
            text = f"👤 *Профиль*\n🆔 ID: `{chat_id}`\n📅 Первый визит: {first}\n💰 Монет: {coins}"
            keyboard = {"inline_keyboard": [[{"text": "🔙 Назад", "callback_data": "menu"}]]}
            send_message(chat_id, text, keyboard)
        elif data == 'games':
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🎲 Кости", "callback_data": "game_dice"}],
                    [{"text": "🏀 Баскетбол", "callback_data": "game_basket"}],
                    [{"text": "🎰 Казино", "callback_data": "game_slot"}],
                    [{"text": "🔙 Назад", "callback_data": "menu"}]
                ]
            }
            send_message(chat_id, "🎮 *Мини-игры*", keyboard)
        elif data == 'menu':
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📊 Статистика", "url": SITE_URL}],
                    [{"text": "👤 Профиль", "callback_data": "profile"}],
                    [{"text": "🎲 Игры", "callback_data": "games"}]
                ]
            }
            send_message(chat_id, "Главное меню:", keyboard)
        elif data.startswith('game_'):
            game = data.split('_')[1]
            users = load_users()
            coins = users.get(str(chat_id), {}).get('coins', 0)
            if game == 'dice':
                val = random.randint(1,6)
                if val == 6:
                    coins += 10
                    res = f"🎲 Выпало 6! +10 монет."
                else:
                    res = f"🎲 Выпало {val}. Повезёт в следующий раз."
            elif game == 'basket':
                if random.randint(1,100) > 70:
                    coins += 15
                    res = "🏀 Попадание! +15 монет."
                else:
                    res = "🏀 Мимо."
            elif game == 'slot':
                sym = ['🍒','🍋','🍊','7️⃣','💎']
                s = [random.choice(sym) for _ in range(3)]
                if s[0]==s[1]==s[2]:
                    coins += 50
                    res = f"🎰 {''.join(s)} ДЖЕКПОТ! +50 монет."
                else:
                    res = f"🎰 {''.join(s)} Попробуй ещё."
            else:
                res = "Неизвестная игра"
            users[str(chat_id)]['coins'] = coins
            save_users(users)
            keyboard = {"inline_keyboard": [[{"text": "🎲 Другие игры", "callback_data": "games"}]]}
            send_message(chat_id, res, keyboard)
    return "ok", 200

if __name__ == "__main__":
    app.run()
