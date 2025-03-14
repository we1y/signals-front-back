import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from app.services.balances import create_or_update_balance
from app.database import get_db
from app.services.users import register_user, create_referral_data
from app.routers.general_routes import get_user_by_telegram_id
from app.services.telegram_service import generate_auth_token

# Загружаем переменные из .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
load_dotenv(dotenv_path)
# Отключаем SQLAlchemy INFO-логи
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)

# Отключаем распространение логов SQLAlchemy (важно!)
logging.getLogger("sqlalchemy.engine").propagate = False
logging.getLogger("sqlalchemy.pool").propagate = False

# Основной логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
# Получаем токен бота
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_API_TOKEN:
    print("Ошибка: не найден токен для Telegram бота в .env файле!")
    exit(1)

# URL вашего сайта
WEBSITE_URL = "https://signals-bot.com"

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user  # Берем данные пользователя
    first_name = user.first_name if user else "Гость"

    start_keyboard = [
        [InlineKeyboardButton("Описание проекта", callback_data="description")],
        [InlineKeyboardButton("Зарегистрироваться", callback_data="register")]
    ]
    start_reply_markup = InlineKeyboardMarkup(start_keyboard)

    if update.message:
        await update.message.reply_text(
            f"Добро пожаловать, {first_name}! Нажмите кнопку, чтобы узнать больше о проекте или зарегистрироваться.",
            reply_markup=start_reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            f"Добро пожаловать, {first_name}! Нажмите кнопку, чтобы узнать больше о проекте или зарегистрироваться.",
            reply_markup=start_reply_markup
        )

async def description(update: Update, context: CallbackContext) -> None:
    # Обрабатываем CallbackQuery, а не сообщение
    callback_query = update.callback_query
    await callback_query.answer()  # Отвечаем на запрос, чтобы убрать "обработан" статус у кнопки

    # Отправляем новое сообщение
    description_keyboard = [
        [InlineKeyboardButton("Начать", callback_data="start_app")],
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    description_reply_markup = InlineKeyboardMarkup(description_keyboard)
    
    await callback_query.message.reply_text(
        "Это описание проекта (заглушка). Здесь будет описание того, как работает проект.",
        reply_markup=description_reply_markup
    )


# Функция для обработки кнопки "Зарегистрироваться"
async def register(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    language_code = user.language_code
    photo_url = getattr(user, 'photo_url', "")

    # Определяем, откуда пришёл запрос
    message = update.message if update.message else update.callback_query.message

    try:
        async with get_db() as db:
            try:
                db_user = await get_user_by_telegram_id(chat_id, db)

                if isinstance(db_user, dict):
                    db_user = await register_user(db, chat_id, username, first_name, last_name, language_code, photo_url)
                    user_id = db_user.id
                    referral_data = await create_referral_data(db, user_id)
                    await create_or_update_balance(db, user_id, balance=100.0, trade_balance=50.0)

                    # Генерация токена для аутентификации
                    token = await generate_auth_token(db, db_user.telegram_id)
                    auth_url = f"{WEBSITE_URL}/auth?token={token}"

                    keyboard = [[InlineKeyboardButton("Открыть мини-приложение", web_app=WebAppInfo(url=auth_url))]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await message.reply_text(
                        f"Привет, {first_name}! Ты успешно зарегистрирован.\n\n"
                        f"Твоя реферальная ссылка: {referral_data.referral_link}\n\n"
                        "Теперь ты можешь использовать наше мини-приложение!",
                        reply_markup=reply_markup
                    )
                else:
                    await message.reply_text(f"Ты уже зарегистрирован, {first_name}!")

            except HTTPException as http_exc:
                logging.error(f"Ошибка при регистрации: {http_exc.detail}")
                await message.reply_text(f"Ошибка регистрации: {http_exc.detail}")

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /register: {e}", exc_info=True)
        await message.reply_text("Произошла ошибка, попробуйте снова.")


# Функция для обработки кнопки "Начать приложение"
async def start_app(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = user.id
    
    # Здесь будет процесс отправки ссылки в мини-приложение
    auth_url = f"{WEBSITE_URL}/auth?token={chat_id}"  # Для примера, использую chat_id в качестве токена
    keyboard = [[InlineKeyboardButton("Открыть мини-приложение", web_app=WebAppInfo(url=auth_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Теперь ты можешь начать использовать наше мини-приложение!",
        reply_markup=reply_markup
    )

async def back_to_start(update: Update, context: CallbackContext) -> None:
    if update.callback_query:
        await update.callback_query.answer()  # Закрываем "зависшую" кнопку

    await start(update, context)  # Передаем сам update, а не message


# Функция для запуска бота
async def main() -> None:
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(description, pattern="description"))
    application.add_handler(CallbackQueryHandler(register, pattern="register"))
    application.add_handler(CallbackQueryHandler(start_app, pattern="start_app"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="back_to_start"))
    
    # Запуск бота
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
