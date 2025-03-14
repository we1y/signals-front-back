from fastapi import FastAPI, HTTPException
import asyncio
import nest_asyncio
from app.database import get_db  # Импортируем функцию для получения сессии
from app.services.signals import process_signals, create_static_signals
from app.services.auto_mode import process_auto_mode_users
from app.routers import users, balances, signals_routes, general_routes  # Подключаем роутеры
from app.telegram_bot import main as start_telegram_bot
from fastapi.middleware.cors import CORSMiddleware
import logging

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
# Применяем nest_asyncio для корректной работы event loop
nest_asyncio.apply()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

app = FastAPI()

# Разрешённые источники (добавьте нужные домены)
origins = [
    "https://signals-bot.com",
    "https://www.signals-bot.com",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Подключаем маршруты
app.include_router(users.router)
app.include_router(balances.router)
app.include_router(signals_routes.signalis_router)
app.include_router(general_routes.router)

@app.on_event("startup")
@app.on_event("startup")
async def startup_event():
    """Запуск фоновых процессов при старте приложения."""
    try:
        logging.info("Запуск фоновых задач.")
        async with get_db() as db:
            await create_static_signals(db)  # Генерация статичных сигналов
        
        # Запуск всех задач одновременно
        asyncio.create_task(start_telegram_bot())  # Telegram бот
        asyncio.create_task(run_background_tasks())  # Фоновые задачи (сигналы + авто-режим)
        
    except Exception as e:
        logging.error(f"Ошибка при запуске фоновых задач: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при запуске фоновых задач")


async def run_background_tasks():
    """Запуск всех фоновых задач в одном процессе."""
    await asyncio.gather(process_signals_task(), run_auto_mode())  # Параллельный запуск




async def process_signals_task():
    """Фоновая задача для обработки сигналов каждые 60 секунд."""
    async with get_db() as db:  # Открываем сессию один раз
        while True:
            try:
                await process_signals(db)  # Переиспользуем сессию
                await asyncio.sleep(60)
            except Exception as e:
                logging.error(f"Ошибка при обработке сигналов: {e}")
                await asyncio.sleep(10)  
            
async def run_auto_mode():
    """Фоновый процесс для обработки пользователей с авто-режимом каждые 60 секунд."""
    while True:
        try:
            async with get_db() as db:  # Получаем сессию через get_db
                await process_auto_mode_users(db)  # Обрабатываем пользователей с авто-режимом
        except Exception as e:
            logging.error(f"Ошибка при обработке авто-режима: {e}")
        await asyncio.sleep(60)  # Асинхронная задержка 60 секунд




@app.get("/")
def read_root():
    """Проверка работы сервера"""
    return {"message": "FastAPI is running!"}
