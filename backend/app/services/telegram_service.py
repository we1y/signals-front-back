import secrets
import logging
from datetime import datetime, timedelta
import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User
from app.models.models import AuthTokens

# Настройка логирования
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.ERROR)  # Уровень логирования INFO для логов

TOKEN_EXPIRATION = timedelta(hours=1)  # Время жизни токена
MOSCOW_TZ = pytz.timezone("Europe/Moscow")  # Часовой пояс Москвы
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
async def generate_auth_token(db: AsyncSession, telegram_id: int) -> str:
    """Генерация или обновление одноразового токена для пользователя по telegram_id"""

    try:
        # Ищем пользователя по telegram_id
        user = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user.scalars().first()

        if not user:
            raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден в базе данных.")

        # Проверяем, есть ли уже активный токен для пользователя
        existing_token = await db.execute(select(AuthTokens).filter(AuthTokens.user_id == telegram_id))
        existing_token = existing_token.scalars().first()

        # Генерация нового безопасного токена
        new_token = secrets.token_urlsafe(32)
        expiration_time_msk = datetime.now(MOSCOW_TZ) + TOKEN_EXPIRATION

        if existing_token:
            # Если токен уже есть, обновляем его и срок действия
            existing_token.token = new_token
            existing_token.expires_at = expiration_time_msk
            logging.info(f"Токен пользователя {telegram_id} обновлен.")
        else:
            # Если токена нет, создаем новый
            auth_token = AuthTokens(user_id=telegram_id, token=new_token, expires_at=expiration_time_msk)
            db.add(auth_token)
            logging.info(f"Новый токен создан для пользователя {telegram_id}.")

        # Сохраняем изменения в базе данных
        await db.commit()

        return new_token

    except Exception as e:
        logging.error(f"Ошибка при генерации токена для пользователя {telegram_id}: {e}", exc_info=True)
        raise


