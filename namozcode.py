import os
import json
import time
import pytz
import threading
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==================== BOT VA BAZA SOZLAMALARI ====================
CONFIG = {
    'bot_token': '8871188277:AAF1TlGsRCadglciubWhlaEVn-frehfxqrI',  # Bot tokeningiz
    'admin_id': 6968399046,                                     # Admin Telegram ID raqami
    'mongo_uri': 'mongodb+srv://javacodex1_db_user:java2011@cluster0.ftgcf62.mongodb.net/?appName=Cluster0',
    'db_name': 'namoz_vaqtlari_bot_db',
    'timezone': 'Asia/Tashkent'                                 # Toshkent vaqti
}

app = Flask(__name__)

# ==================== TIL MATNLARI VA SO'ZLIKLAR ====================
TEXTS = {
    'uz_lat': {
        'welcome': (
            "<b>Assalomu alaykum va rahmatullohi va barakatuh!</b>\n\n"
            "🕌 <b>Namoz vaqtlari botiga xush kelibsiz!</b>\n\n"
            "📅 <i>Bugungi namoz vaqtlari:</i>\n"
            " <b>Bomdod:</b> <code>{bomdod}</code>\n"
            " <b>Peshin:</b> <code>{peshin}</code>\n"
            " <b>Asr:</b> <code>{asr}</code>\n"
            " <b>Shom:</b> <code>{shom}</code>\n"
            " <b>Xufton:</b> <code>{xufton}</code>\n\n"
            "👇 <i>Kerakli namoz haqida ma'lumot olish uchun tugmalardan foydalaning:</i>"
        ),
        'btn_bomdod': " BOMDOD 🌅 NAMOZI",
        'btn_peshin': " PESHIN ☀️ NAMOZI",
        'btn_asr': " ASR 🏞️ NAMOZI",
        'btn_shom': " SHOM 🌄 NAMOZI",
        'btn_xufton': " XUFTON 🌑 NAMOZI",
        'btn_lang': "🌐 Tilni o'zgartirish",
        'choose_lang_title': "Iltimos, tilni tanlang / Илтимос, тилни танланг / Пожалуйста, выберите язык:",
        'info_title': "{badge} <b>{name} NAMOZI</b>\n\n⏰ <b>Vaqti:</b> <code>{time}</code>\n📖 <b>Rakatlar tartibi:</b> {rakat}\n\n🔔 <i>Vaqti kirishi bilan bot sizga avtomatik eslatma yuboradi.</i>",
        'rakat_bomdod': "2 rakat sunnat, 2 rakat farz",
        'rakat_peshin': "4 rakat sunnat, 4 rakat farz, 2 rakat sunnat",
        'rakat_asr': "4 rakat farz",
        'rakat_shom': "3 rakat farz, 2 rakat sunnat",
        'rakat_xufton': "4 rakat farz, 2 rakat sunnat, 3 rakat vitr",
        'notify': (
            "ASSALOMU ALEYKUM VA RAHMATULULLOHI VA BARAKATUH\n"
            "NAMOZ VAQTI BOʻLDI\n"
            "{name}  : {time}"
        )
    },
    'uz_cyr': {
        'welcome': (
            "<b>Ассалому алайкум ва раҳматуллоҳи ва баракатуҳ!</b>\n\n"
            "🕌 <b>Намоз вақтлари ботига хуш келибсиз!</b>\n\n"
            "📅 <i>Бугунги намоз вақтлари:</i>\n"
            " <b>Бомдод:</b> <code>{bomdod}</code>\n"
            " <b>Пешин:</b> <code>{peshin}</code>\n"
            " <b>Аср:</b> <code>{asr}</code>\n"
            " <b>Шом:</b> <code>{shom}</code>\n"
            " <b>Хуфтон:</b> <code>{xufton}</code>\n\n"
            "👇 <i>Керакли намоз ҳақида маълумот олиш учун тугмалардан фойдаланинг:</i>"
        ),
        'btn_bomdod': " БОМДОД 🌅 НАМОЗИ",
        'btn_peshin': " ПЕШИН ☀️ НАМОЗИ",
        'btn_asr': " АСР 🏞️ НАМОЗИ",
        'btn_shom': " ШОМ 🌄 НАМОЗИ",
        'btn_xufton': " ХУФТОН 🌑 НАМОЗИ",
        'btn_lang': "🌐 Тилни ўзгартириш",
        'choose_lang_title': "Илтимос, тилни танланг / Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        'info_title': "{badge} <b>{name} НАМОЗИ</b>\n\n⏰ <b>Вақти:</b> <code>{time}</code>\n📖 <b>Ракатлар тартиби:</b> {rakat}\n\n🔔 <i>Вақти кириши билан бот сизга автоматик эслатма юборади.</i>",
        'rakat_bomdod': "2 ракат суннат, 2 ракат фарз",
        'rakat_peshin': "4 ракат суннат, 4 ракат фарз, 2 ракат суннат",
        'rakat_asr': "4 ракат фарз",
        'rakat_shom': "3 ракат фарз, 2 ракат суннат",
        'rakat_xufton': "4 ракат фарз, 2 ракат суннат, 3 ракат витр",
        'notify': (
            "АССАЛОМУ АЛАЙКУМ ВА РАҲМАТУЛЛОҲИ ВА БАРАКАТУҲ\n"
            "НАМОЗ ВАҚТИ БЎЛДИ\n"
            "{name}  : {time}"
        )
    },
    'ru': {
        'welcome': (
            "<b>Ассаламу алейкум ва рахматуллахи ва баракатух!</b>\n\n"
            "🕌 <b>Добро пожаловать в бот времени намаза!</b>\n\n"
            "📅 <i>Расписание на сегодня:</i>\n"
            " <b>Фаджр (Бомдod):</b> <code>{bomdod}</code>\n"
            " <b>Зухр (Пeshin):</b> <code>{peshin}</code>\n"
            " <b>Аsr:</b> <code>{asr}</code>\n"
            " <b>Мagриб (Шom):</b> <code>{shom}</code>\n"
            " <b>Иshа (Хufton):</b> <code>{xufton}</code>\n\n"
            "👇 <i>Нажмите на кнопки ниже для получения подробностей:</i>"
        ),
        'btn_bomdod': " ФАДЖР (БОМДОД) 🌅",
        'btn_peshin': " ЗУХР (ПЕШИН) ☀️",
        'btn_asr': " АСР 🏞️",
        'btn_shom': " МАГРИБ (ШОМ) 🌄",
        'btn_xufton': " ИША (ХУФТОН) 🌑",
        'btn_lang': "🌐 Изменить язык",
        'choose_lang_title': "Пожалуйста, выберите язык / Iltimos, tilni tanlang / Илтимос, тилни танланг:",
        'info_title': "{badge} <b>{name}</b>\n\n⏰ <b>Время:</b> <code>{time}</code>\n📖 <b>Порядок ракаатов:</b> {rakat}\n\n🔔 <i>При наступлении времени намаза бот отправит вам напоминание.</i>",
        'rakat_bomdod': "2 ракаата сунны, 2 ракаата фарда",
        'rakat_peshin': "4 ракаата сунны, 4 ракаата фарда, 2 ракаата сунны",
        'rakat_asr': "4 ракаата фарда",
        'rakat_shom': "3 ракаата фарда, 2 ракаата сунны",
        'rakat_xufton': "4 ракаата фарда, 2 ракаата сунны, 3 ракаата витр",
        'notify': (
            "АССАЛАМУ АЛЕЙКУМ ВА РАХМАТУЛЛАХИ ВА БАРАКАТУХ\n"
            "ВРЕМЯ НАМАЗА НАСТУПИЛО\n"
            "{name}  : {time}"
        )
    }
}

# ==================== TELEGRAM API FUNKSIYASI ====================
def telegram_api(method, params=None):
    if params is None:
        params = {}
    url = f"https://api.telegram.org/bot{CONFIG['bot_token']}/{method}"
    try:
        response = requests.post(url, json=params, timeout=15)
        return response.json()
    except Exception as e:
        logging.error(f"Telegram API Xatolik ({method}): {e}")
        return None

# ==================== MA'LUMOTLAR BAZASI ====================
class Database:
    _instance = None

    def __init__(self):
        self.client = MongoClient(
            CONFIG['mongo_uri'],
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        self.db = self.client[CONFIG['db_name']]
        self.users = self.db['users']
        self.settings = self.db['settings']
        self.user_states = self.db['user_states']
        self.init_defaults()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init_defaults(self):
        try:
            self.users.create_index("user_id", unique=True)
            self.user_states.create_index("user_id", unique=True)
            
            default_times = {
                "_id": "namoz_times",
                "bomdod": "05:10",
                "peshin": "12:40",
                "asr": "17:15",
                "shom": "19:00",
                "xufton": "20:30"
            }
            if not self.settings.find_one({"_id": "namoz_times"}):
                self.settings.insert_one(default_times)
        except Exception as e:
            logging.warning(f"DB Init Warning: {e}")

    def add_or_update_user(self, user_id, first_name="", username=""):
        user_id_str = str(user_id)
        self.users.update_one(
            {"user_id": user_id_str},
            {"$set": {
                "first_name": first_name,
                "username": username,
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "user_id": user_id_str,
                "lang": None,  # Til hali tanlanmagan
                "joined_at": datetime.utcnow(),
                "status": "active"
            }},
            upsert=True
        )

    def get_user(self, user_id):
        return self.users.find_one({"user_id": str(user_id)})

    def set_user_lang(self, user_id, lang):
        self.users.update_one(
            {"user_id": str(user_id)},
            {"$set": {"lang": lang}},
            upsert=True
        )

    def get_user_lang(self, user_id):
        u = self.get_user(user_id)
        if u and u.get('lang'):
            return u['lang']
        return 'uz_lat'

    def get_all_users(self):
        return list(self.users.find({"status": "active"}))

    def get_users_count(self):
        return self.users.count_documents({})

    def get_namoz_times(self):
        res = self.settings.find_one({"_id": "namoz_times"})
        if not res:
            return {
                "bomdod": "05:10",
                "peshin": "12:40",
                "asr": "17:15",
                "shom": "19:00",
                "xufton": "20:30"
            }
        return res

    def update_namoz_time(self, namoz_key, time_str):
        self.settings.update_one(
            {"_id": "namoz_times"},
            {"$set": {namoz_key: time_str}},
            upsert=True
        )

    def set_state(self, user_id, state, temp_data=None):
        self.user_states.update_one(
            {"user_id": str(user_id)},
            {"$set": {
                "user_id": str(user_id),
                "state": state,
                "temp_data": temp_data
            }},
            upsert=True
        )

    def get_state(self, user_id):
        return self.user_states.find_one({"user_id": str(user_id)})

    def clear_state(self, user_id):
        self.user_states.delete_one({"user_id": str(user_id)})

# ==================== BOT BOSHQARUV SINF ====================
class NamozBot:
    def __init__(self):
        self.db = Database.get_instance()
        self.admin_id = str(CONFIG['admin_id'])

    def is_admin(self, user_id):
        return str(user_id) == self.admin_id

    def get_language_keyboard(self):
        """ Til tanlash tugmalari: Рус🇷🇺 / Узбек🇺🇿 / Uzbek🇺🇿 """
        return {
            "inline_keyboard": [
                [
                    {"text": "Рус 🇷🇺", "callback_data": "set_lang_ru"},
                    {"text": "Узбек 🇺🇿", "callback_data": "set_lang_uz_cyr"}
                ],
                [
                    {"text": "Uzbek 🇺🇿", "callback_data": "set_lang_uz_lat"}
                ]
            ]
        }

    def get_main_menu_keyboard(self, user_id):
        lang = self.db.get_user_lang(user_id)
        t = TEXTS.get(lang, TEXTS['uz_lat'])

        keyboard = [
            [t['btn_bomdod'], t['btn_peshin']],
            [t['btn_asr'], t['btn_shom']],
            [t['btn_xufton']],
            [t['btn_lang']]
        ]
        
        if self.is_admin(user_id):
            keyboard.append(["⚙️ ADMIN PANEL"])

        return {
            "keyboard": [[{"text": btn} for btn in row] for row in keyboard],
            "resize_keyboard": True,
            "persistent": True
        }

    def handle_update(self, update):
        if 'message' in update:
            self.handle_message(update['message'])
        elif 'callback_query' in update:
            self.handle_callback_query(update['callback_query'])

    def handle_message(self, message):
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        chat_type = chat.get('type', 'private')

        # Kanal yoki guruhlarga tegmaslik uchun filtr
        if chat_type != 'private':
            return

        from_user = message.get('from', {})
        user_id = from_user.get('id')
        if not user_id:
            return

        text = message.get('text', '').strip()
        first_name = from_user.get('first_name', '')
        username = from_user.get('username', '')
        
        self.db.add_or_update_user(user_id, first_name, username)
        user_data = self.db.get_user(user_id)

        # Bekor qilish
        if text == '/cancel':
            self.db.clear_state(user_id)
            telegram_api('sendMessage', {
                'chat_id': chat_id,
                'text': "❌ Amal bekor qilindi.",
                'reply_markup': self.get_main_menu_keyboard(user_id)
            })
            return

        # Holatni tekshirish (Admin vaqt o'zgartirishi yoki rassilka)
        user_state = self.db.get_state(user_id)
        if user_state and user_state.get('state'):
            state_name = user_state['state']
            if state_name.startswith('awaiting_time_'):
                namoz_key = state_name.replace('awaiting_time_', '')
                self.process_time_input(chat_id, user_id, namoz_key, text)
                return
            elif state_name == 'awaiting_broadcast':
                self.process_broadcast(chat_id, user_id, message)
                return

        # Til tanlash menyusi
        if text.startswith('/start') or not user_data.get('lang'):
            if not user_data.get('lang') or text == '/start':
                self.send_language_selection(chat_id)
                return

        lang = self.db.get_user_lang(user_id)
        t = TEXTS.get(lang, TEXTS['uz_lat'])

        # Tilni o'zgartirish tugmasi bosilganda
        if text in ["🌐 Tilni o'zgartirish", "🌐 Тилни ўзгартириш", "🌐 Изменить язык", "/lang"]:
            self.send_language_selection(chat_id)
            return

        # Admin panel
        if (text == '⚙️ ADMIN PANEL' or text == '/admin') and self.is_admin(user_id):
            self.send_admin_panel(chat_id)
            return

        # Namoz tugmalari tekshiruvi (barcha 3 tilda ishlaydi)
        times = self.db.get_namoz_times()
        upper_text = text.upper()

        if "BOMDOD" in upper_text or "БОМДОД" in upper_text or "ФАDЖР" in upper_text:
            name = "BOMDOD" if lang == 'uz_lat' else ("БОМДOД" if lang == 'uz_cyr' else "ФАDЖР (БOМDOD)")
            self.send_namoz_info(chat_id, name, "", times.get('bomdod', '05:10'), t['rakat_bomdod'])
            return
        elif "PESHIN" in upper_text or "ПEШIN" in upper_text or "ЗУХR" in upper_text:
            name = "PESHIN" if lang == 'uz_lat' else ("ПEШIN" if lang == 'uz_cyr' else "ЗУХR (ПEШIN)")
            self.send_namoz_info(chat_id, name, "", times.get('peshin', '12:40'), t['rakat_peshin'])
            return
        elif "ASR" in upper_text or "АСР" in upper_text:
            name = "ASR" if lang == 'uz_lat' else ("АСР" if lang == 'uz_cyr' else "АСР")
            self.send_namoz_info(chat_id, name, "", times.get('asr', '17:15'), t['rakat_asr'])
            return
        elif "SHOM" in upper_text or "ШОМ" in upper_text or "МАГРИБ" in upper_text:
            name = "SHOM" if lang == 'uz_lat' else ("ШОМ" if lang == 'uz_cyr' else "МАГРИБ (ШОМ)")
            self.send_namoz_info(chat_id, name, "", times.get('shom', '19:00'), t['rakat_shom'])
            return
        elif "XUFTON" in upper_text or "ХУФТОН" in upper_text or "ИША" in upper_text:
            name = "XUFTON" if lang == 'uz_lat' else ("ХУФТОН" if lang == 'uz_cyr' else "ИША (ХУФТОН)")
            self.send_namoz_info(chat_id, name, "", times.get('xufton', '20:30'), t['rakat_xufton'])
            return

        # Agar boshqa biror xabar yozilsa
        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': "👇 Iltimos, tugmalardan birini tanlang / Илтимос, тугмалардан бирини танланг:",
            'reply_markup': self.get_main_menu_keyboard(user_id)
        })

    def send_language_selection(self, chat_id):
        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': "Tilni tanlang / Тилни танланг / Выберите язык:\n\n🇺🇿 <b>Uzbek</b> / 🇺🇿 <b>Узбек</b> / 🇷🇺 <b>Рус</b>",
            'parse_mode': 'HTML',
            'reply_markup': self.get_language_keyboard()
        })

    def send_namoz_info(self, chat_id, name, color_badge, time_val, rakat_info):
        user_lang = self.db.get_user_lang(chat_id)
        t = TEXTS.get(user_lang, TEXTS['uz_lat'])

        text = t['info_title'].format(
            badge=color_badge,
            name=name,
            time=time_val,
            rakat=rakat_info
        )
        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        })

    def send_welcome_screen(self, chat_id, user_id):
        lang = self.db.get_user_lang(user_id)
        t = TEXTS.get(lang, TEXTS['uz_lat'])
        times = self.db.get_namoz_times()

        msg = t['welcome'].format(
            bomdod=times.get('bomdod', '05:10'),
            peshin=times.get('peshin', '12:40'),
            asr=times.get('asr', '17:15'),
            shom=times.get('shom', '19:00'),
            xufton=times.get('xufton', '20:30')
        )

        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'HTML',
            'reply_markup': self.get_main_menu_keyboard(user_id)
        })

    # ==================== ADMIN PANEL ====================
    def send_admin_panel(self, chat_id, edit_message_id=None):
        times = self.db.get_namoz_times()
        total_users = self.db.get_users_count()

        text = (
            "👑 <b>БОТ АДМИН ПАНЕЛИ</b>\n\n"
            f"👥 <b>Жами обуначилар:</b> <code>{total_users}</code> та\n\n"
            "⏰ <b>Ҳозирги намоз вақтлари:</b>\n"
            f" Бомдod: <code>{times.get('bomdod')}</code>\n"
            f" Пeshin: <code>{times.get('peshin')}</code>\n"
            f" Аsr: <code>{times.get('asr')}</code>\n"
            f" Шom: <code>{times.get('shom')}</code>\n"
            f" Хufton: <code>{times.get('xufton')}</code>\n\n"
            "<i>Ўзгартирмоқчи бўлган намозингизни танланг:</i>"
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": f" Бомdod ({times.get('bomdod')})", "callback_data": "edit_bomdod"},
                    {"text": f" Пeshin ({times.get('peshin')})", "callback_data": "edit_peshin"}
                ],
                [
                    {"text": f" Аср ({times.get('asr')})", "callback_data": "edit_asr"},
                    {"text": f" Шом ({times.get('shom')})", "callback_data": "edit_shom"}
                ],
                [
                    {"text": f" Хуфтон ({times.get('xufton')})", "callback_data": "edit_xufton"}
                ],
                [
                    {"text": "📊 Батафсил статистика", "callback_data": "admin_stats"},
                    {"text": "✉️ Барчага хабар юбориш", "callback_data": "admin_broadcast"}
                ]
            ]
        }

        if edit_message_id:
            telegram_api('editMessageText', {
                'chat_id': chat_id,
                'message_id': edit_message_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            })
        else:
            telegram_api('sendMessage', {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            })

    def handle_callback_query(self, cb):
        cb_id = cb['id']
        message = cb.get('message', {})
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        message_id = message.get('message_id')
        user_id = cb.get('from', {}).get('id')
        data = cb.get('data')

        # Til tanlash callback
        if data.startswith('set_lang_'):
            selected_lang = data.replace('set_lang_', '')
            self.db.set_user_lang(user_id, selected_lang)

            telegram_api('answerCallbackQuery', {
                'callback_query_id': cb_id,
                'text': "✅ Til tanlandi / Тил танланди / Язык выбран!"
            })

            # Avvalgi inline xabarni o'chirib, yangi asosiy menyuni yuborish
            telegram_api('deleteMessage', {'chat_id': chat_id, 'message_id': message_id})
            self.send_welcome_screen(chat_id, user_id)
            return

        # Faqat admin uchun bo'lgan qismlar
        if not self.is_admin(user_id):
            telegram_api('answerCallbackQuery', {
                'callback_query_id': cb_id,
                'text': "❌ Сиз admin эмассиз!",
                'show_alert': True
            })
            return

        if data.startswith('edit_'):
            namoz_key = data.replace('edit_', '')
            namoz_names = {
                'bomdod': ' БОМДОД',
                'peshin': ' ПЕШИН',
                'asr': ' АСР',
                'shom': ' ШОМ',
                'xufton': ' ХУФТОН'
            }
            n_name = namoz_names.get(namoz_key, namoz_key)

            self.db.set_state(user_id, f'awaiting_time_{namoz_key}')

            text = (
                f"✍️ <b>{n_name} намозининг янги вақтини киритинг:</b>\n\n"
                f"<i>Формат:</i> <code>HH:MM</code> (Масалан: <code>05:10</code> ёки <code>18:45</code>)\n\n"
                f"❌ Бекор қилиш учун /cancel ни босинг."
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Бекор қилиш ва қайтиш", "callback_data": "admin_back"}]
                ]
            }

            telegram_api('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            })
            telegram_api('answerCallbackQuery', {'callback_query_id': cb_id})
            return

        if data == 'admin_stats':
            total = self.db.get_users_count()
            text = (
                "📊 <b>БОТ СТАТИСТИКАСИ</b>\n\n"
                f"👥 <b>Жами фаол фойдаланувчилар:</b> <code>{total}</code> та\n"
                f"🕒 <b>Сервер вақт минтақаси:</b> <code>Asia/Tashkent</code>\n"
                f"⚡ <b>Бот ҳолати:</b> Ишламоқда (Online)"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Орқага", "callback_data": "admin_back"}]
                ]
            }
            telegram_api('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            })
            telegram_api('answerCallbackQuery', {'callback_query_id': cb_id})
            return

        if data == 'admin_broadcast':
            self.db.set_state(user_id, 'awaiting_broadcast')
            text = (
                "✉️ <b>Барча фойдаланувчиларга хабар юбориш:</b>\n\n"
                "Юбормоқчи бўлган хабарингизни ёзинг (матн, расм ёки видео юборишингиз мумкин).\n\n"
                "❌ Бекор қилиш учун /cancel ни босинг."
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Бекор қилиш", "callback_data": "admin_back"}]
                ]
            }
            telegram_api('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            })
            telegram_api('answerCallbackQuery', {'callback_query_id': cb_id})
            return

        if data == 'admin_back':
            self.db.clear_state(user_id)
            self.send_admin_panel(chat_id, message_id)
            telegram_api('answerCallbackQuery', {'callback_query_id': cb_id})
            return

    def process_time_input(self, chat_id, user_id, namoz_key, text):
        import re
        match = re.match(r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$', text.strip())
        if not match:
            telegram_api('sendMessage', {
                'chat_id': chat_id,
                'text': "❌ <b>Нотўғри формат!</b> Илтимос, вақтни <code>HH:MM</code> шаклида киритинг (масалан: <code>05:10</code>):",
                'parse_mode': 'HTML'
            })
            return

        h, m = match.groups()
        formatted_time = f"{int(h):02d}:{int(m):02d}"

        self.db.update_namoz_time(namoz_key, formatted_time)
        self.db.clear_state(user_id)

        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': f"✅ <b>Муваффақиятли сақланди!</b>\n\nЯнги вақт: <code>{formatted_time}</code>",
            'parse_mode': 'HTML',
            'reply_markup': self.get_main_menu_keyboard(user_id)
        })
        self.send_admin_panel(chat_id)

    def process_broadcast(self, chat_id, user_id, message):
        self.db.clear_state(user_id)
        users = self.db.get_all_users()
        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': f"⏳ <i>Хабар {len(users)} та фойдаланувчига тарқатилмоқда...</i>",
            'parse_mode': 'HTML'
        })

        count = 0
        for u in users:
            uid = u.get('user_id')
            res = telegram_api('copyMessage', {
                'chat_id': uid,
                'from_chat_id': chat_id,
                'message_id': message['message_id']
            })
            if res and res.get('ok'):
                count += 1
            time.sleep(0.04)

        telegram_api('sendMessage', {
            'chat_id': chat_id,
            'text': f"✅ <b>Хабар тарқатилди!</b>\n\nЖами: <code>{count}</code> та фойдаланувчига етказилди.",
            'parse_mode': 'HTML',
            'reply_markup': self.get_main_menu_keyboard(chat_id)
        })
        self.send_admin_panel(chat_id)

# ==================== AVTOMATIK NAMOZ ESLATMASI CRON ====================
def namoz_scheduler_loop(bot: NamozBot):
    logging.info("⏰ Namoz vaqtlari avtomatik kuzatuv tizimi ishga tushdi...")
    tz = pytz.timezone(CONFIG['timezone'])
    last_notified_minute = {}

    namoz_labels_map = {
        'bomdod': {'uz_lat': 'BOMDOD 🌅', 'uz_cyr': 'БОМДОД 🌅', 'ru': 'ФАДЖР (БОМДОД) 🌅'},
        'peshin': {'uz_lat': 'PESHIN ☀️', 'uz_cyr': 'ПЕШИН ☀️', 'ru': 'ЗУХР (ПЕШИН) ☀️'},
        'asr': {'uz_lat': 'ASR 🏞️', 'uz_cyr': 'АСР 🏞️', 'ru': 'АСР 🏞️'},
        'shom': {'uz_lat': 'SHOM 🌄', 'uz_cyr': 'ШОМ 🌄', 'ru': 'МАГРИБ (ШОМ) 🌄'},
        'xufton': {'uz_lat': 'XUFTON 🌑', 'uz_cyr': 'ХУФТОН 🌑', 'ru': 'ИША (ХУФТОН) 🌑'}
    }

    while True:
        try:
            now = datetime.now(tz)
            current_hm = now.strftime('%H:%M')
            current_date_hm = now.strftime('%Y-%m-%d_%H:%M')

            times = bot.db.get_namoz_times()

            for key, t_val in times.items():
                if key not in namoz_labels_map:
                    continue

                norm_t_val = ":".join([f"{int(x):02d}" for x in t_val.split(":")]) if ":" in str(t_val) else str(t_val)

                if current_hm == norm_t_val:
                    if last_notified_minute.get(key) != current_date_hm:
                        last_notified_minute[key] = current_date_hm

                        users = bot.db.get_all_users()
                        logging.info(f"📢 [{key}] Namoz vaqti keldi! {len(users)} ta odamga yuborilmoqda...")

                        for u in users:
                            uid = u.get('user_id')
                            user_lang = u.get('lang') or 'uz_lat'
                            label = namoz_labels_map[key].get(user_lang, namoz_labels_map[key]['uz_lat'])
                            
                            t = TEXTS.get(user_lang, TEXTS['uz_lat'])
                            notification_text = t['notify'].format(name=label, time=t_val)

                            telegram_api('sendMessage', {
                                'chat_id': uid,
                                'text': notification_text
                            })
                            time.sleep(0.04)
        except Exception as e:
            logging.error(f"Scheduler Xatolik: {e}")

        time.sleep(15)

# ==================== FLASK SERVER VA LONG POLLING ====================
bot_instance = NamozBot()

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "bot": "Namoz Vaqtlari Boti Faol!"}), 200

@app.route('/', methods=['POST'])
def webhook():
    if request.is_json:
        update = request.get_json()
        if update:
            bot_instance.handle_update(update)
    return jsonify({"status": "ok"}), 200

def start_polling():
    logging.info("🚀 Polling ishga tushdi...")
    telegram_api('deleteWebhook', {'drop_pending_updates': False})
    offset = 0
    while True:
        try:
            updates = telegram_api('getUpdates', {'offset': offset, 'timeout': 20})
            if updates and updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    bot_instance.handle_update(update)
        except Exception as e:
            logging.error(f"Polling loop error: {e}")
            time.sleep(3)

if __name__ == '__main__':
    # 1. Avtomat vaqt tekshiruvchi fon oqimi
    scheduler_thread = threading.Thread(target=namoz_scheduler_loop, args=(bot_instance,), daemon=True)
    scheduler_thread.start()

    # 2. Polling oqimi
    polling_thread = threading.Thread(target=start_polling, daemon=True)
    polling_thread.start()

    # 3. Flask veb server
    app.run(host='0.0.0.0', port=5000, debug=False)
