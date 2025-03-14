from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
load_dotenv(dotenv_path)
# Отключаем информационные логи SQLAlchemy
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

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в .env файле!")

# Строка подключения для asyncpg
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Создаем асинхронный sessionmaker для SQLAlchemy
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Создаём базовый класс для моделей
Base = declarative_base()

# Если у вас есть отдельный Base для 'lazy load' моделей
BaseReferral = declarative_base()

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db  # Возвращаем сессию для работы с ней
        except Exception as e:
            # Если ошибка — откатываем изменения
            await db.rollback()
            raise  # Поднимаем исключение дальше
        finally:
            # Гарантируем, что сессия будет закрыта
            await db.close()
