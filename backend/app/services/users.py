import random
import string
import logging
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.models import User, Referrals
from app.database import get_db


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

# Функция генерации уникального реферального кода
async def generate_unique_referral_code(db: AsyncSession, user_id: int, telegram_id: int) -> str:
    while True:
        # Используем telegram_id вместо случайного кода
        referral_link = f"https://app.com/ref/{user_id}-{telegram_id}"

        # Проверяем, не существует ли уже такая реферальная ссылка
        result = await db.execute(select(Referrals).filter(Referrals.referral_link == referral_link))
        existing_referral = result.scalars().first()

        if not existing_referral:
            logging.info(f"Генерирован уникальный реферальный код для пользователя {user_id} с telegram_id {telegram_id}: {referral_link}")
            return referral_link


    
# Функция для создания реферальной записи
async def create_referral_data(db: AsyncSession, user_id: int, referrer_id: int = None):
    try:

        # Проверяем, есть ли уже реферальная запись
        result = await db.execute(select(Referrals).filter(Referrals.user_id == user_id))
        existing_referral = result.scalars().first()

        if existing_referral:
            return existing_referral

        # Получаем пользователя
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logging.error(f"Не найден пользователь с ID {user_id}. Операция отменена.")
            return None

        # Генерируем уникальную реферальную ссылку с использованием telegram_id
        referral_link = await generate_unique_referral_code(db, user_id, user.telegram_id)

        # Проверяем реферера, если он указан
        referrer = None
        if referrer_id:
            result = await db.execute(select(User).filter(User.id == referrer_id))
            referrer = result.scalars().first()

            if not referrer:
                logging.warning(f"Реферер с ID {referrer_id} не найден, запись будет создана без реферера.")
                referrer_id = None  # Если реферера нет, оставляем поле пустым

        # Создаем запись в таблице Referrals
        new_referral = Referrals(
            user_id=user_id,
            telegram_id=user.telegram_id,
            referral_link=referral_link,
            referrer_id=referrer_id,  # используем правильное имя поля
            invited_count=0,
            referred_by=referrer_id  # исправляем на правильное поле
        )

        db.add(new_referral)

        # Если есть реферер — увеличиваем ему счетчик приглашенных
        if referrer_id:
            referrer_referral = await db.execute(select(Referrals).filter(Referrals.user_id == referrer_id))
            referrer_ref = referrer_referral.scalars().first()

            if referrer_ref:
                referrer_ref.invited_count += 1
                logging.info(f"Увеличен счетчик приглашенных у пользователя {referrer_id}.")

        await db.commit()
        await db.refresh(new_referral)

        return new_referral

    except SQLAlchemyError as e:
        logging.error(f"Ошибка при создании реферальной записи для {user_id}: {e}", exc_info=True)
        await db.rollback()
        return None


# Функция для регистрации пользователя
async def register_user(db: AsyncSession, chat_id: int, username: str, first_name: str, last_name: str, 
                        language_code: str, photo_url: str = None):
    try:
        logging.info(f"Пытаемся зарегистрировать пользователя с chat_id: {chat_id}")

        # Проверяем, существует ли пользователь с таким chat_id
        result = await db.execute(select(User).filter(User.telegram_id == chat_id))
        db_user = result.scalars().first()

        if not db_user:
            # Если пользователя нет, создаем нового
            db_user = User(
                telegram_id=chat_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                photo_url=photo_url,  # Обработка photo_url, если оно передано
                automod=False,  # Устанавливаем automod в False
                plan=0,  # Устанавливаем plan в 0
                reinvestements_par=0,  # ✅ Добавлено поле reinvestements_par с дефолтным значением
                in_work = 0
            )
            db.add(db_user)
            await db.commit()  # Коммитим нового пользователя
            await db.refresh(db_user)
        else:
            logging.info(f"")

        return db_user
    except Exception as e:
        logging.error(f"Ошибка при регистрации пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при регистрации пользователя")



async def add_referral(db: AsyncSession, telegram_id: int, referral_link: str):
    """
    Добавляет пользователя в реферальную систему.

    :param db: Асинхронная сессия SQLAlchemy.
    :param telegram_id: Telegram ID того, кого добавляем.
    :param referral_link: Реферальная ссылка (Telegram ID пригласившего).
    
    :return: Объект Referrals, если успешно, иначе None.
    """
    try:

        # Извлекаем telegram_id из referral_link (например, если ссылка вида "https://app.com/ref/27-5592773679")
        referrer_telegram_id = extract_telegram_id_from_link(referral_link)

        # Ищем пригласившего пользователя по его Telegram ID
        referrer_result = await db.execute(select(User).filter(User.telegram_id == referrer_telegram_id))
        referrer = referrer_result.scalars().first()

        if not referrer:
            logging.warning(f"Пользователь с referral_link {referral_link} не найден.")
            return None

        # Проверяем, существует ли уже пользователь с таким telegram_id
        existing_user = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        existing_user = existing_user.scalars().first()

        if existing_user:
            logging.warning(f"Пользователь с telegram_id {telegram_id} уже существует.")
            return None  # Если пользователь уже существует, ничего не делаем

        # Создаем нового пользователя в таблице Users, если он еще не существует
        new_user = User(
            telegram_id=telegram_id,  # Telegram ID пользователя
            username="",               # Здесь можно добавить логику для получения других данных, если нужно
            first_name="",
            last_name="",
            language_code="en",  # Можно оставить по умолчанию или изменить в зависимости от данных
            is_bot=False
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)  # Получаем объект нового пользователя

        # Создаем запись в таблице Referrals для нового пользователя
        new_referral = Referrals(
            user_id=new_user.id,           # ID нового пользователя в системе
            telegram_id=telegram_id,       # Telegram ID приглашенного
            referral_link=referral_link,   # Ссылка с реферальным кодом
            referred_by=referrer.id        # ID пригласившего пользователя (ссылается на пользователя)
        )
        db.add(new_referral)

        # Увеличиваем счетчик приглашенных у реферера
        referrer_ref_result = await db.execute(select(Referrals).filter(Referrals.user_id == referrer.id))
        referrer_ref = referrer_ref_result.scalars().first()

        if referrer_ref:
            referrer_ref.invited_count += 1

        await db.commit()
        await db.refresh(new_referral)

        return new_referral

    except SQLAlchemyError as e:
        logging.error(f"Ошибка при добавлении реферала {telegram_id}: {e}", exc_info=True)
        await db.rollback()
        return None


def extract_telegram_id_from_link(referral_link: str) -> int:
    """
    Извлекает telegram_id из реферальной ссылки.
    Например, если ссылка в формате: 'https://app.com/ref/27-5592773679',
    то извлекается 5592773679.
    """
    try:
        parts = referral_link.split('/')
        # Получаем часть, которая является telegram_id, например: '27-5592773679'
        return int(parts[-1].split('-')[-1])  # Возвращаем только последний числовой элемент
    except Exception as e:
        logging.error(f"Ошибка при извлечении Telegram ID из ссылки {referral_link}: {e}")
        return None

