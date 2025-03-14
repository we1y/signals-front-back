import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from fastapi import Depends

# Отключаем SQLAlchemy INFO-логи
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)

# Основной логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# Функция для получения сессии
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as db:
        try:
            yield db  # Возвращаем сессию для работы с ней
        finally:
            await db.close()  # Закрытие сессии после завершения работы с ней
