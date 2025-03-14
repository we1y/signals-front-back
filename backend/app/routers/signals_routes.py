from datetime import datetime, timedelta
import logging
import os
import random
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.services.get_db import get_db  # Импортируем get_db
from app.models.models import User, Balance, Signal, SignalInvestment
from app.services.balances import freeze_balance, update_trading_balance
from app.services.signals import create_signal  # Импортируем метод создания сигнала

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

# Настройка логирования в файл logs_signals.txt (рядом с main)
log_file_path = os.path.join(os.path.dirname(__file__), "../logs_signals.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

signalis_router = APIRouter(prefix="/api/signals", tags=["Signals"])

### 🔹 **Pydantic-модель для запроса**
class JoinSignalRequest(BaseModel):
    telegram_id: int
    signal_id: int

class CustomSignalRequest(BaseModel):
    name: str
    join_time: int
    active_time: int
    burn_chance: float
    profit_percent: float
    signal_cost: int  # Добавили параметр цены входа

class RandomSignalRequest(BaseModel):
    name: str  # Имя сигнала

# Минимальное время блокировки перед выходом (3 минуты)
MIN_LOCK_PERIOD_MINUTES = 3

#-------------------------------------------------------------------------#   

@signalis_router.post("/join")
async def join_signal(request: JoinSignalRequest, db: AsyncSession = Depends(get_db)):
    """ 
    Пользователь входит в сигнал. Средства списываются с торгового баланса 
    и фиксируются в инвестициях. 
    """
    telegram_id = request.telegram_id
    signal_id = request.signal_id

    try:
        # Получаем пользователя
        user_result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user_result.scalars().first()
        if not user:
            return {"message": "User not found", "success": False}

        # Проверяем, не заходил ли пользователь уже в этот сигнал
        existing_investment = await db.execute(
            select(SignalInvestment).filter(
                SignalInvestment.user_id == user.id,
                SignalInvestment.signal_id == signal_id
            )
        )
        if existing_investment.scalars().first():
            return {"message": "User has already joined this signal", "success": False}

        # Получаем баланс пользователя
        balance_result = await db.execute(select(Balance).filter(Balance.user_id == user.id))
        balance = balance_result.scalars().first()
        if not balance:
            return {"message": "Balance not found", "success": False}

        # Проверяем доступность сигнала
        signal_result = await db.execute(select(Signal).filter(Signal.id == signal_id, Signal.join_until > func.now()))
        signal = signal_result.scalars().first()

        # Если сигнал не доступен
        if not signal:
            return {
                "message": "Signal is not available for joining",
                "success": False,
                "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "signal_join_until": signal.join_until.strftime("%Y-%m-%d %H:%M:%S") if signal else "N/A"
            }

        # Получаем стоимость входа
        signal_cost = signal.signal_cost

        # Проверяем баланс
        if balance.trade_balance < signal_cost:
            return {
                "message": "Insufficient trading balance for signal cost",
                "success": False,
                "required_amount": signal_cost,
                "current_balance": balance.trade_balance
            }

        # Вычитаем сумму с торгового баланса
        balance.trade_balance -= signal_cost

        # Увеличиваем количество активных сигналов у пользователя
        user.in_work += 1

        # Сохраняем инвестицию
        investment = SignalInvestment(
            signal_id=signal_id,
            user_id=user.id,
            amount=signal_cost,
        )
        db.add(investment)

        await db.commit()

        return {
            "message": "Successfully joined the signal",
            "success": True,
            "signal_id": signal_id,
            "amount": signal_cost
        }

    except Exception as e:
        logging.error(f"Error while joining signal: {str(e)}")
        return {"message": "An error occurred while joining the signal", "success": False}

    
#-------------------------------------------------------------------------#   

### 🔹 **Создание случайного сигнала**
# Структура запроса для случайного сигнала
class RandomSignalRequest(BaseModel):
    name: str

@signalis_router.post("/create_random")
async def create_random_signal(request: RandomSignalRequest, db: AsyncSession = Depends(get_db)):
    """Создает случайный сигнал со случайными параметрами (время до входа, продолжительность, шанс сгорания, процент прибыли, цена входа)."""
    name = request.name

    # Генерация случайных параметров
    join_time = random.randint(60, 600)  # 1-10 минут до входа
    active_time = random.randint(600, 3600)  # 10-60 минут активное время
    profit_percent = round(random.uniform(4, 60), 2)  # 4-60% прибыли
    
    # Увеличение риска прямо пропорционально прибыли
    burn_chance = round(profit_percent * random.uniform(0.5, 1.5), 2)  # Риск = 50-150% от прибыли

    # Ограничиваем риск в пределах 5-90%
    burn_chance = min(max(burn_chance, 5), 90)

    signal_cost = random.randint(100, 1000)  # Цена входа от 100 до 1000

    try:
        signal = await create_signal(db, name, join_time, active_time, burn_chance, profit_percent, signal_cost)
    
        return {
            "message": "Random signal created successfully",
            "signal_id": signal.id,
            "name": signal.name,
            "join_until": signal.join_until,
            "expires_at": signal.expires_at,
            "burn_chance": burn_chance,
            "profit_percent": profit_percent,
            "signal_cost": signal_cost
        }
    except Exception as e:
        logging.error(f"Error while creating random signal {name}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while creating a random signal.")

    
#-------------------------------------------------------------------------#   

@signalis_router.post("/create_custom")
async def create_custom_signal(request: CustomSignalRequest, db: AsyncSession = Depends(get_db)):
    """Создает сигнал с пользовательскими параметрами (время до входа, продолжительность, шанс сгорания, процент прибыли, цена входа)."""
    name = request.name
    join_time = request.join_time
    active_time = request.active_time
    profit_percent = request.profit_percent
    signal_cost = request.signal_cost

    # Проверка валидности значений
    if join_time <= 0 or active_time <= 0 or profit_percent < 4 or profit_percent > 60:
        raise HTTPException(status_code=400, detail="Invalid parameters: join_time and active_time must be > 0, profit_percent must be between 4 and 60")
    
    if signal_cost < 100 or signal_cost > 1000:
        raise HTTPException(status_code=400, detail="Invalid signal_cost: must be between 100 and 1000")

    # Автоматический расчет риска на основе прибыли (50-150% от прибыли)
    burn_chance = round(profit_percent * random.uniform(0.5, 1.5), 2)

    # Ограничиваем риск в пределах 5-90%
    burn_chance = min(max(burn_chance, 5), 90)

    try:
        signal = await create_signal(db, name, join_time, active_time, burn_chance, profit_percent, signal_cost)

        return {
            "message": "Custom signal created successfully",
            "signal_id": signal.id,
            "name": signal.name,
            "join_until": signal.join_until,
            "expires_at": signal.expires_at,
            "burn_chance": burn_chance,
            "profit_percent": profit_percent,
            "signal_cost": signal_cost
        }
    except Exception as e:
        logging.error(f"Error while creating custom signal {name}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while creating a custom signal.")

    
#-------------------------------------------------------------------------#   

@signalis_router.get("/active")
async def get_active_signals(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """ Получает список активных сигналов в зависимости от плана пользователя. """
    try:
        # Получаем пользователя по Telegram ID
        user_result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Определяем, сколько сигналов можно вернуть в зависимости от плана
        signals_limit = {0: 2, 1: 4, 2: 5}.get(user.plan, 2)

        # Получаем активные сигналы
        active_signals_result = await db.execute(
            select(Signal).filter(Signal.join_until > func.now()).limit(signals_limit)
        )
        active_signals = active_signals_result.scalars().all()

        if not active_signals:
            return {"message": "No active signals available."}

        signals_data = [
            {
                "signal_id": signal.id,
                "name": signal.name,
                "join_until": signal.join_until,
                "burn_chance": signal.burn_chance,  # Исправлена опечатка (bur_chance → burn_chance)
                "expires_at": signal.expires_at,
                "signal_cost": signal.signal_cost,
                "profit_percent": signal.profit_percent  # ✅ Добавлено отображение прибыли
            }
            for signal in active_signals
        ]
        
        return {"active_signals": signals_data}

    except Exception as e:
        logging.error(f"Error retrieving active signals: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving active signals.")


#-------------------------------------------------------------------------#   
@signalis_router.get("/investments/{telegram_id}")
async def get_user_investments(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """
    Ищет user_id по telegram_id, затем получает все инвестиции пользователя.
    """
    # 1. Ищем user_id по telegram_id
    user_result = await db.execute(select(User.id).filter(User.telegram_id == telegram_id))
    user = user_result.scalar()

    if not user:
        return {"message": "Пользователь не найден"}

    # 2. Ищем все инвестиции пользователя
    investments_result = await db.execute(select(SignalInvestment).filter(SignalInvestment.user_id == user))
    investments = investments_result.scalars().all()

    if not investments:
        return {"message": "У пользователя нет инвестиций"}

    # 3. Формируем ответ
    return {
        "user_id": user,
        "investments": [
            {
                "id": inv.id,
                "signal_id": inv.signal_id,
                "amount": inv.amount,
                "profit": inv.profit,
                "created_at": inv.created_at,
            }
            for inv in investments
        ]
    }

#-------------------------------------------------------------------------#   

@signalis_router.post("/enable_automode")
async def enable_automode(telegram_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user_result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user_result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.automod:
            return {"message": "Auto mode is already enabled", "success": False}

        balance_result = await db.execute(select(Balance).filter(Balance.user_id == user.id))
        balance = balance_result.scalars().first()

        if not balance:
            raise HTTPException(status_code=404, detail="Balance not found")

        signal_result = await db.execute(select(Signal).filter(Signal.join_until > func.now()).order_by(Signal.join_until).limit(1))
        signal = signal_result.scalars().first()

        if not signal:
            return {"message": "No available signals", "success": False}

        signal_cost = signal.signal_cost

        if balance.trade_balance < signal_cost:
            return {
                "message": "Insufficient trading balance for signal cost",
                "success": False,
                "required_amount": signal_cost,
                "current_balance": balance.trade_balance
            }

        balance.trade_balance -= signal_cost
        user.in_work += 1

        investment = SignalInvestment(
            signal_id=signal.id,
            user_id=user.id,
            amount=signal_cost,
            auto_mode=True,
        )
        db.add(investment)

        user.automod = True
        user.auto_mode_locked_until = datetime.utcnow() + timedelta(minutes=MIN_LOCK_PERIOD_MINUTES)
        user.updated_at = datetime.utcnow()
        db.add(user)

        await db.commit()

        next_exit_time = user.auto_mode_locked_until.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "message": "Auto mode successfully enabled and joined the signal",
            "success": True,
            "next_available_exit": next_exit_time
        }

    except Exception as e:
        logging.error(f"Error while enabling auto mode: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while enabling auto mode")

    
#-------------------------------------------------------------------------# 
@signalis_router.post("/disable_automode")
async def disable_automode(telegram_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user_result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user_result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.automod:
            return {"message": "Auto mode is already disabled", "success": False}

        current_time = datetime.utcnow()
        if user.auto_mode_locked_until and current_time < user.auto_mode_locked_until:
            return {
                "message": "Auto mode cannot be disabled yet. Try again later.",
                "success": False,
                "next_available_exit": user.auto_mode_locked_until.strftime("%Y-%m-%d %H:%M:%S")
            }

        user.automod = False
        user.auto_mode_locked_until = None
        user.updated_at = datetime.utcnow()
        db.add(user)

        # Закрываем инвестицию, если она есть
        investment_result = await db.execute(select(SignalInvestment).filter(SignalInvestment.user_id == user.id, SignalInvestment.auto_mode == True))
        investments = investment_result.scalars().all()
        for investment in investments:
            # Закрытие инвестиции (например, статус или другие операции)
            pass

        await db.commit()

        return {"message": "Auto mode successfully disabled", "success": True}

    except Exception as e:
        logging.error(f"Error while disabling auto mode: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while disabling auto mode")