import telebot
import pandas as pd
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import os
import logging
import time
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Loglashni sozlash (Railway.app uchun stdout ga yo'naltirish)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')  # Loglarni faylga ham yozish uchun
    ]
)

# Get TOKEN from environment variables
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logging.error("TOKEN environment variable not set")
    raise ValueError("TOKEN environment variable not set")

# Admin foydalanuvchilar ro'yxati (Telegram user ID)
ADMINS = os.getenv('ADMINS', '').split(',')
ADMINS = [int(admin_id) for admin_id in ADMINS if admin_id.strip().isdigit()]

bot = telebot.TeleBot(TOKEN)

EXCEL_FILE = 'products.xlsx'
CSV_FILE = 'products.csv'

SUCCESS_STICKER = 'CAACAgIAAxkBAAIBG2YJ5qGf...'
ERROR_STICKER = 'CAACAgIAAxkBAAIBH2YJ5qH...'

# Foydalanuvchi tillarini saqlash uchun lug'at
user_languages = {}
# Foydalanuvchi holatini saqlash uchun lug'at
user_state = {}

# Excel yoki CSV faylni o'qish
def read_excel():
    try:
        if os.path.exists(CSV_FILE):
            logging.info(f"{CSV_FILE} fayli topildi, o'qilmoqda...")
            df = pd.read_csv(CSV_FILE, encoding='utf-8')
            logging.info("CSV fayl muvaffaqiyatli o'qildi.")
            print("Ustun nomlari (CSV):", df.columns.tolist())
            return df

        if os.path.exists(EXCEL_FILE):
            logging.info(f"{EXCEL_FILE} fayli topildi, CSV ga aylantirilmoqda...")
            df = pd.read_excel(EXCEL_FILE)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8')
            logging.info(f"{EXCEL_FILE} fayli {CSV_FILE} ga aylantirildi.")
            print("Ustun nomlari (Excel -> CSV):", df.columns.tolist())
            return df
        else:
            logging.error(f"{EXCEL_FILE} fayli topilmadi.")
            print(f"{EXCEL_FILE} fayli topilmadi.")
            return pd.DataFrame(columns=['Shipment Tracking Code', 'Shipping Name', 'Package Number', 'Weight/KG', 'Quantity', 'Flight', 'Customer code'])

    except Exception as e:
        logging.error(f"Faylni o'qishda xatolik: {str(e)}")
        print(f"Faylni o'qishda xatolik: {e}")
        return pd.DataFrame(columns=['Shipment Tracking Code', 'Shipping Name', 'Package Number', 'Weight/KG', 'Quantity', 'Flight', 'Customer code'])

# Ma'lumotlarni trek kodi bo'yicha qidirish
def search_product_by_trek_code(code):
    df = read_excel()
    try:
        code = str(code).strip().lower()
    except ValueError:
        pass
    if 'Shipment Tracking Code' in df.columns:
        df['Shipment Tracking Code'] = df['Shipment Tracking Code'].astype(str).str.strip().str.lower()
        result = df[df['Shipment Tracking Code'] == code]
        if not result.empty:
            return result[['Shipping Name', 'Package Number', 'Weight/KG', 'Quantity', 'Flight', 'Customer code']].to_dict('records')
        return None
    else:
        logging.error("Xatolik: 'Shipment Tracking Code' ustuni topilmadi.")
        print("Xatolik: 'Shipment Tracking Code' ustuni topilmadi.")
        return None

# Ma'lumotlarni mijoz kodi bo'yicha qidirish
def search_product_by_customer_code(code):
    df = read_excel()
    try:
        code = str(code).strip().lower()
    except ValueError:
        pass
    if 'Customer code' in df.columns:
        df['Customer code'] = df['Customer code'].astype(str).str.strip().str.lower()
        result = df[df['Customer code'] == code]
        if not result.empty:
            return result[['Shipment Tracking Code', 'Shipping Name', 'Package Number', 'Weight/KG', 'Quantity', 'Flight', 'Customer code']].to_dict('records')
        return None
    else:
        logging.error("Xatolik: 'Customer code' ustuni topilmadi.")
        print("Xatolik: 'Customer code' ustuni topilmadi.")
        return None

# Foydalanuvchi tilini aniqlash
def get_user_language(user_id):
    return user_languages.get(user_id, 'uz')

# Tugma matnlarini tilga qarab qaytarish
def get_button_text(user_id, button_key):
    buttons = {
        'search': {'uz': "Yukni qidirish 📦", 'ru': "Поиск груза 📦"},
        'feedback': {'uz': "Izoh qoldiring 📝", 'ru': "Оставить отзыв 📝"},
        'contacts': {'uz': "Manzil va kontaktlar 📍", 'ru': "Адрес и контакты 📍"},
        'language': {'uz': "Tilni tanlang 🌐", 'ru': "Выбрать язык 🌐"},
        'uzbek': {'uz': "O'zbek 🇺🇿", 'ru': "Узбекский 🇺🇿"},
        'russian': {'uz': "Русский 🇷🇺", 'ru': "Русский 🇷🇺"},
        'back': {'uz': "Orqaga qaytish 🔙", 'ru': "Вернуться назад 🔙"},
        'by_trek_code': {'uz': "Trek kodi orqali 🔍", 'ru': "По трек-коду 🔍"},
        'by_customer_code': {'uz': "Mijoz kodi orqali 🔎", 'ru': "По коду клиента 🔎"},
        'admin_panel': {'uz': "Admin paneli ⚙️", 'ru': "Панель администратора ⚙️"}
    }
    lang = get_user_language(user_id)
    return buttons[button_key][lang]

# Foydalanuvchi admin ekanligini tekshirish
def is_admin(user_id):
    return user_id in ADMINS

# Asosiy menyuni yaratish
def main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_button_text(user_id, 'search')))
    markup.add(KeyboardButton(get_button_text(user_id, 'feedback')))
    markup.add(KeyboardButton(get_button_text(user_id, 'contacts')))
    markup.add(KeyboardButton(get_button_text(user_id, 'language')))
    if is_admin(user_id):
        markup.add(KeyboardButton(get_button_text(user_id, 'admin_panel')))
    return markup

# Yuk qidirish bo'limi uchun maxsus menyu
def search_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_button_text(user_id, 'by_trek_code')))
    markup.add(KeyboardButton(get_button_text(user_id, 'by_customer_code')))
    markup.add(KeyboardButton(get_button_text(user_id, 'back')))
    return markup

# Trek kodi yoki mijoz kodi kiritish uchun menyu
def code_input_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_button_text(user_id, 'back')))
    return markup

# Izoh qoldirish bo'limi uchun menyu
def feedback_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_button_text(user_id, 'back')))
    return markup

# Admin paneli menyusi
def admin_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Yangi database yuklash 📂"))
    markup.add(KeyboardButton(get_button_text(user_id, 'back')))
    return markup

# Start komandasi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_state[user_id] = 'main'
    lang = get_user_language(user_id)
    welcome_msg = {
        'uz': (
            "Assalomu alaykum! 🎉\n"
            "Bu bot orqali JET CARGO yuklari haqida ma'lumot olishingiz mumkin\n"
            "Quyidagi tugmalardan birini tanlang:"
        ),
        'ru': (
            "Здравствуйте! 🎉\n"
            "С помощью этого бота JET CARGO вы можете найти информацию о своём грузе.\n"
            "Выберите одну из кнопок ниже:"
        )
    }
    bot.reply_to(message, welcome_msg[lang], reply_markup=main_menu(user_id))

# Izoh qoldirish funksiyasi
def handle_feedback(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    user_state[user_id] = 'feedback'
    prompt_msg = {'uz': "Iltimos, izohingizni yozing:", 'ru': "Пожалуйста, напишите ваш отзыв:"}
    bot.reply_to(message, prompt_msg[lang], reply_markup=feedback_menu(user_id))
    bot.register_next_step_handler(message, save_feedback)

def save_feedback(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    feedback = message.text
    
    if feedback == get_button_text(user_id, 'back'):
        user_state[user_id] = 'main'
        back_msg = {'uz': "Asosiy menyuga qaytdingiz.", 'ru': "Вы вернулись в главное меню."}
        bot.reply_to(message, back_msg[lang], reply_markup=main_menu(user_id))
        return
    
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id}: {feedback}\n")
    success_msg = {'uz': "Rahmat! Izohingiz qabul qilindi. ✅", 'ru': "Спасибо! Ваш отзыв принят. ✅"}
    bot.reply_to(message, success_msg[lang], reply_markup=main_menu(user_id))
    user_state[user_id] = 'main'

# Manzil va kontaktlar funksiyasi
def show_contacts(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    contact_info = {
        'uz': (
            "📍 Manzil: Toshkent sh., Chilanzar tumani, Arnasoy 5A\n"
            "📞 Telefon: +998 99-981-22-72\n"
            "📩 Telegram: @jetcargoo\n"
            "📷 Instagram: https://www.instagram.com/jetcargoo"
        ),
        'ru': (
            "📍 Адрес: г. Ташкент, Чиланзарский район, Арнасай 5А\n"
            "📞 Телефон: +998 99-981-22-72\n"
            "📩 Telegram: @jetcargoo\n"
            "📷 Instagram: https://www.instagram.com/jetcargoo"
        )
    }
    bot.reply_to(message, contact_info[lang], reply_markup=main_menu(user_id))

# Tilni tanlash funksiyasi
def select_language(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    prompt_msg = {'uz': "Iltimos, tilni tanlang:", 'ru': "Пожалуйста, выберите язык:"}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_button_text(user_id, 'uzbek')), KeyboardButton(get_button_text(user_id, 'russian')))
    markup.add(KeyboardButton(get_button_text(user_id, 'back')))
    bot.reply_to(message, prompt_msg[lang], reply_markup=markup)
    bot.register_next_step_handler(message, set_language)

def set_language(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    if message.text == get_button_text(user_id, 'back'):
        user_state[user_id] = 'main'
        back_msg = {'uz': "Asosiy menyuga qaytdingiz.", 'ru': "Вы вернулись в главное меню."}
        bot.reply_to(message, back_msg[lang], reply_markup=main_menu(user_id))
        return
    if message.text in ["O'zbek 🇺🇿", "Узбекский 🇺🇿"]:
        user_languages[user_id] = 'uz'
        success_msg = {'uz': "Til O'zbek tiliga o'zgartirildi! 🇺🇿", 'ru': "Язык изменён на узбекский! 🇺🇿"}
    elif message.text in ["Русский 🇷🇺"]:
        user_languages[user_id] = 'ru'
        success_msg = {'uz': "Til Rus tiliga o'zgartirildi! 🇷🇺", 'ru': "Язык изменён на русский! 🇷🇺"}
    else:
        error_msg = {'uz': "Iltimos, tilni to'g'ri tanlang.", 'ru': "Пожалуйста, выберите язык правильно."}
        bot.reply_to(message, error_msg[lang], reply_markup=main_menu(user_id))
        return
    bot.reply_to(message, success_msg[lang], reply_markup=main_menu(user_id))

# Admin paneli funksiyasi
def handle_admin_panel(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    if not is_admin(user_id):
        error_msg = {
            'uz': "Sizda admin huquqlari yo'q.",
            'ru': "У вас нет прав администратора."
        }
        bot.reply_to(message, error_msg[lang], reply_markup=main_menu(user_id))
        return
    
    user_state[user_id] = 'admin_panel'
    prompt_msg = {
        'uz': "Admin paneliga xush kelibsiz! Quyidagi amallardan birini tanlang:",
        'ru': "Добро пожаловать в панель администратора! Выберите одно из действий:"
    }
    bot.reply_to(message, prompt_msg[lang], reply_markup=admin_menu(user_id))
    bot.register_next_step_handler(message, process_admin_action)

# Admin harakatlarini qayta ishlash
def process_admin_action(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    action = message.text
    
    if action == get_button_text(user_id, 'back'):
        user_state[user_id] = 'main'
        back_msg = {'uz': "Asosiy menyuga qaytdingiz.", 'ru': "Вы вернулись в главное меню."}
        bot.reply_to(message, back_msg[lang], reply_markup=main_menu(user_id))
        return
    
    if action == "Yangi database yuklash 📂":
        prompt_msg = {
            'uz': "Iltimos, yangi database faylini (.xlsx yoki .csv) yuboring:",
            'ru': "Пожалуйста, отправьте новый файл базы данных (.xlsx или .csv):"
        }
        bot.reply_to(message, prompt_msg[lang], reply_markup=code_input_menu(user_id))
        bot.register_next_step_handler(message, handle_database_upload)
    else:
        error_msg = {
            'uz': "Noto'g'ri buyruq. Iltimos, quyidagi tugmalardan birini tanlang:",
            'ru': "Неверная команда. Пожалуйста, выберите одну из кнопок ниже:"
        }
        bot.reply_to(message, error_msg[lang], reply_markup=admin_menu(user_id))
        bot.register_next_step_handler(message, process_admin_action)

# Yangi database faylini yuklash
@bot.message_handler(content_types=['document'])
def handle_database_upload(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    if not is_admin(user_id):
        error_msg = {
            'uz': "Sizda fayl yuklash huquqi yo'q.",
            'ru': "У вас нет прав для загрузки файла."
        }
        bot.reply_to(message, error_msg[lang], reply_markup=main_menu(user_id))
        return
    
    if user_state.get(user_id) != 'admin_panel':
        error_msg = {
            'uz': "Fayl yuklash uchun avval admin paneliga kiring.",
            'ru': "Для загрузки файла сначала войдите в панель администратора."
        }
        bot.reply_to(message, error_msg[lang], reply_markup=main_menu(user_id))
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name
        
        if not file_name.endswith(('.xlsx', '.csv')):
            error_msg = {
                'uz': "Faqat .xlsx yoki .csv fayllarni yuklash mumkin.",
                'ru': "Можно загружать только файлы .xlsx или .csv."
            }
            bot.reply_to(message, error_msg[lang], reply_markup=admin_menu(user_id))
            bot.register_next_step_handler(message, process_admin_action)
            return
        
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            logging.info(f"Eski {CSV_FILE} fayli o'chirildi.")
        
        if file_name.endswith('.xlsx'):
            temp_excel = 'temp_products.xlsx'
            with open(temp_excel, 'wb') as new_file:
                new_file.write(downloaded_file)
            df = pd.read_excel(temp_excel)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8')
            os.remove(temp_excel)
            logging.info(f"Yangi .xlsx fayli {CSV_FILE} ga aylantirildi va saqlandi.")
        else:
            with open(CSV_FILE, 'wb') as new_file:
                new_file.write(downloaded_file)
            logging.info(f"Yangi .csv fayli {CSV_FILE} sifatida saqlandi.")
        
        success_msg = {
            'uz': "✅ Yangi database muvaffaqiyatli yuklandi va saqlandi!",
            'ru': "✅ Новая база данных успешно загружена и сохранена!"
        }
        bot.reply_to(message, success_msg[lang], reply_markup=admin_menu(user_id))
        bot.register_next_step_handler(message, process_admin_action)
    
    except Exception as e:
        logging.error(f"Faylni yuklashda xatolik: {str(e)}")
        error_msg = {
            'uz': f"Faylni yuklashda xato yuz berdi: {str(e)}",
            'ru': f"Ошибка при загрузке файла: {str(e)}"
        }
        bot.reply_to(message, error_msg[lang], reply_markup=admin_menu(user_id))
        bot.register_next_step_handler(message, process_admin_action)

# Yuk qidirish turini tanlash
def select_search_type(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    user_state[user_id] = 'select_search_type'
    prompt_msg = {
        'uz': "Qanday qidirishni xohlaysiz?",
        'ru': "Как хотите искать груз?"
    }
    bot.reply_to(message, prompt_msg[lang], reply_markup=search_menu(user_id))

# Trek kodi bo'yicha qidirish
def search_by_trek_code(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    codes_input = message.text.strip()
    
    if codes_input == get_button_text(user_id, 'back'):
        user_state[user_id] = 'select_search_type'
        back_msg = {'uz': "Qidirish turini tanlashga qaytdingiz.", 'ru': "Вы вернулись к выбору типа поиска."}
        bot.reply_to(message, back_msg[lang], reply_markup=search_menu(user_id))
        return
    
    codes = [code.strip() for code in codes_input.replace(',', ' ').split() if code.strip()]
    
    if not codes:
        error_msg = {
            'uz': "Iltimos, trek kodini kiriting.",
            'ru': "Пожалуйста, введите трек-код."
        }
        bot.reply_to(message, error_msg[lang], reply_markup=code_input_menu(user_id))
        bot.register_next_step_handler(message, search_by_trek_code)
        return
    
    response = ""
    found_any = False
    
    for code in codes:
        results = search_product_by_trek_code(code)
        if results:
            found_any = True
            for item in results:
                result_msg = {
                    'uz': (
                        f"\n✅ Yuk topildi! (Trek kodi: {code})\n\n"
                        f"📦 Mahsulot: {item['Shipping Name']}\n"
                        f"📏 Paket raqami: {item['Package Number']}\n"
                        f"⚖️ Vazn: {item['Weight/KG']} kg\n"
                        f"🔢 Miqdor: {item['Quantity']}\n"
                        f"✈️ Parvoz: {item['Flight']}\n"
                        f"👤 Mijoz kodi: {item['Customer code']}\n"
                    ),
                    'ru': (
                        f"\n✅ Груз найден! (Трек-код: {code})\n\n"
                        f"📦 Товар: {item['Shipping Name']}\n"
                        f"📏 Номер пакета: {item['Package Number']}\n"
                        f"⚖️ Вес: {item['Weight/KG']} кг\n"
                        f"🔢 Количество: {item['Quantity']}\n"
                        f"✈️ Рейс: {item['Flight']}\n"
                        f"👤 Код клиента: {item['Customer code']}\n"
                    )
                }
                response += result_msg[lang]
        else:
            error_msg = {
                'uz': f"❌ {code} trek kodiga mos yuk topilmadi.\n",
                'ru': f"❌ Груз с трек-кодом {code} не найден.\n"
            }
            response += error_msg[lang]
    
    try:
        bot.reply_to(message, response.strip())
        time.sleep(0.5)
        if found_any:
            bot.send_sticker(message.chat.id, SUCCESS_STICKER)
        else:
            bot.send_sticker(message.chat.id, ERROR_STICKER)
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Xabar yuborishda xato: {str(e)}")
        error_msg = {
            'uz': "Xabar yuborishda xato yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
            'ru': "Ошибка при отправке сообщения. Пожалуйста, попробуйте снова позже."
        }
        bot.reply_to(message, error_msg[lang])
    
    bot.register_next_step_handler(message, search_by_trek_code)

# Mijoz kodi bo'yicha qidirish
def search_by_customer_code(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    code = message.text.strip()
    
    if code == get_button_text(user_id, 'back'):
        user_state[user_id] = 'select_search_type'
        back_msg = {'uz': "Qidirish turini tanlashga qaytdingiz.", 'ru': "Вы вернулись к выбору типа поиска."}
        bot.reply_to(message, back_msg[lang], reply_markup=search_menu(user_id))
        return
    
    if not code:
        error_msg = {
            'uz': "Iltimos, mijoz kodini kiriting.",
            'ru': "Пожалуйста, введите код клиента."
        }
        bot.reply_to(message, error_msg[lang], reply_markup=code_input_menu(user_id))
        bot.register_next_step_handler(message, search_by_customer_code)
        return
    
    results = search_product_by_customer_code(code)
    response = ""
    found_any = False
    
    if results:
        found_any = True
        header_msg = {
            'uz': f"📋 Mijoz kodi: {code} bo'yicha barcha yuklar ro'yxati:",
            'ru': f"📋 Список всех грузов по коду клиента: {code}:"
        }
        try:
            bot.reply_to(message, header_msg[lang])
            time.sleep(0.5)
        except telebot.apihelper.ApiTelegramException as e:
            logging.error(f"Xabar yuborishda xato: {str(e)}")
            error_msg = {
                'uz': "Xabar yuborishda xato yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
                'ru': "Ошибка при отправке сообщения. Пожалуйста, попробуйте снова позже."
            }
            bot.reply_to(message, error_msg[lang])
            return
        
        for idx, item in enumerate(results, 1):
            result_msg = {
                'uz': (
                    f"📦 Yuk #{idx}\n"
                    f"🔢 Trek kodi: {item['Shipment Tracking Code']}\n"
                    f"📦 Mahsulot: {item['Shipping Name']}\n"
                    f"📏 Paket raqami: {item['Package Number']}\n"
                    f"⚖️ Vazn: {item['Weight/KG']} kg\n"
                    f"🔢 Miqdor: {item['Quantity']}\n"
                    f"✈️ Parvoz: {item['Flight']}\n"
                    f"👤 Mijoz kodi: {item['Customer code']}\n"
                    f"{'-'*30}"
                ),
                'ru': (
                    f"📦 Груз #{idx}\n"
                    f"🔢 Трек-код: {item['Shipment Tracking Code']}\n"
                    f"📦 Товар: {item['Shipping Name']}\n"
                    f"📏 Номер пакета: {item['Package Number']}\n"
                    f"⚖️ Вес: {item['Weight/KG']} кг\n"
                    f"🔢 Количество: {item['Quantity']}\n"
                    f"✈️ Рейс: {item['Flight']}\n"
                    f"👤 Код клиента: {item['Customer code']}\n"
                    f"{'-'*30}"
                )
            }
            try:
                bot.reply_to(message, result_msg[lang])
                time.sleep(0.5)
            except telebot.apihelper.ApiTelegramException as e:
                logging.error(f"Yuk #{idx} xabarini yuborishda xato: {str(e)}")
                error_msg = {
                    'uz': f"Yuk #{idx} ma'lumotini yuborishda xato yuz berdi.",
                    'ru': f"Ошибка при отправке информации о грузе #{idx}."
                }
                bot.reply_to(message, error_msg[lang])
    else:
        error_msg = {
            'uz': f"❌ {code} mijoz kodiga mos yuk topilmadi.",
            'ru': f"❌ Груз с кодом клиента {code} не найден."
        }
        try:
            bot.reply_to(message, error_msg[lang])
            time.sleep(0.5)
        except telebot.apihelper.ApiTelegramException as e:
            logging.error(f"Xabar yuborishda xato: {str(e)}")
            error_msg = {
                'uz': "Xabar yuborishda xato yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
                'ru': "Ошибка при отправке сообщения. Пожалуйста, попробуйте снова позже."
            }
            bot.reply_to(message, error_msg[lang])
    
    try:
        time.sleep(0.5)
        if found_any:
            bot.send_sticker(message.chat.id, SUCCESS_STICKER)
        else:
            bot.send_sticker(message.chat.id, ERROR_STICKER)
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Stiker yuborishda xato: {str(e)}")
    
    bot.register_next_step_handler(message, search_by_customer_code)

# Xabar ishlovchisi
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    search_text = get_button_text(user_id, 'search')
    feedback_text = get_button_text(user_id, 'feedback')
    contacts_text = get_button_text(user_id, 'contacts')
    language_text = get_button_text(user_id, 'language')
    admin_panel_text = get_button_text(user_id, 'admin_panel')
    by_trek_code_text = get_button_text(user_id, 'by_trek_code')
    by_customer_code_text = get_button_text(user_id, 'by_customer_code')
    back_text = get_button_text(user_id, 'back')

    if user_state.get(user_id) == 'search_by_trek_code':
        search_by_trek_code(message)
        return
    
    if user_state.get(user_id) == 'search_by_customer_code':
        search_by_customer_code(message)
        return
    
    if user_state.get(user_id) == 'feedback':
        save_feedback(message)
        return
    
    if user_state.get(user_id) == 'select_search_type':
        if message.text == by_trek_code_text:
            user_state[user_id] = 'search_by_trek_code'
            prompt_msg = {
                'uz': "Trek kodni kiriting:",
                'ru': "Введите трек-код:"
            }
            bot.reply_to(message, prompt_msg[lang], reply_markup=code_input_menu(user_id))
            bot.register_next_step_handler(message, search_by_trek_code)
        elif message.text == by_customer_code_text:
            user_state[user_id] = 'search_by_customer_code'
            prompt_msg = {
                'uz': "Mijoz kodini kiriting:",
                'ru': "Введите код клиента:"
            }
            bot.reply_to(message, prompt_msg[lang], reply_markup=code_input_menu(user_id))
            bot.register_next_step_handler(message, search_by_customer_code)
        elif message.text == back_text:
            user_state[user_id] = 'main'
            back_msg = {'uz': "Asosiy menyuga qaytdingiz.", 'ru': "Вы вернулись в главное меню."}
            bot.reply_to(message, back_msg[lang], reply_markup=main_menu(user_id))
        return
    
    if user_state.get(user_id) == 'admin_panel':
        process_admin_action(message)
        return

    if message.text == search_text:
        select_search_type(message)
    elif message.text == feedback_text:
        handle_feedback(message)
    elif message.text == contacts_text:
        show_contacts(message)
    elif message.text == language_text:
        select_language(message)
    elif message.text == admin_panel_text and is_admin(user_id):
        handle_admin_panel(message)
    else:
        error_msg = {
            'uz': "Iltimos, quyidagi tugmalardan birini tanlang:",
            'ru': "Пожалуйста, выберите одну из кнопок ниже:"
        }
        bot.reply_to(message, error_msg[lang], reply_markup=main_menu(user_id))

# Botni ishga tushirish
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Bot pollingda xatolik: {str(e)}")
        print(f"Xatolik yuz berdi: {e}")
        time.sleep(5)
        bot.polling(none_stop=True)