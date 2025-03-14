import logging
import os
import random
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import pytz
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.models import Profit, Signal, SignalInvestment, Balance, User
from app.services.balances import freeze_balance, unfreeze_balance, update_trading_balance

# Получаем параметры из .env
PROFIT_PERCENT = float(os.getenv("PROFIT_PERCENT", 1.01))
BURN_CHANCE = float(os.getenv("BURN_CHANCE", 0.1))
JOIN_TIME = int(os.getenv("JOIN_TIME", 300))
ACTIVE_TIME = int(os.getenv("ACTIVE_TIME", 1800))

logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)
MAX_SECONDS = 10 * 365 * 24 * 60 * 60

def current_moscow_time():
    return datetime.now(timezone.utc) + timedelta(hours=3)

async def create_signal(
    db: AsyncSession,
    name: str,
    join_time: int,
    active_time: int,
    burn_chance: float,
    profit_percent: float,
    signal_cost: int  # Добавили стоимость сигнала
):
    if join_time > MAX_SECONDS or active_time > MAX_SECONDS:
        raise ValueError("join_time или active_time слишком велики! Максимум — 10 лет.")
    
    try:
        now = current_moscow_time()
        join_until = now + timedelta(seconds=join_time)
        expires_at = join_until + timedelta(seconds=active_time)
        
        signal = Signal(
            name=name,
            join_until=join_until,
            expires_at=expires_at,
            burn_chance=burn_chance,
            profit_percent=profit_percent,
            signal_cost=signal_cost  # Теперь явно указываем стоимость сигнала
        )
        db.add(signal)
        await db.commit()
        return signal
    except Exception as e:
        await db.rollback()
        logging.error(f"Ошибка при создании сигнала: {e}")
        raise e


async def create_static_signals(db: AsyncSession):
    try:
        # Удаляем старые статичные сигналы
        await db.execute(text("DELETE FROM signals WHERE name LIKE 'Статичный сигнал%'"))
        await db.commit()

        # Сбрасываем последовательность ID
        await db.execute(text("SELECT setval(pg_get_serial_sequence('signals', 'id'), COALESCE(MAX(id), 1), false) FROM signals"))
        await db.commit()

        for i in range(9):
            profit = random.uniform(4, 60) / 100  # Переводим процент прибыли в доли (от 0.04 до 0.6)
            risk = min(0.1 + profit * 1.2, 0.95)  # Пропорционально увеличиваем риск (максимум 95%)

            work_time = 20 * 60  # 20 минут
            signal_cost = random.randint(100, 200)  # Стоимость сигнала

            join_time = 15 * 60  # 15 минут до входа
            active_time = work_time  # Время истечения

            # Текущее московское время
            current_time = current_moscow_time() + timedelta(hours=3)

            # Создаем сигнал
            signal = Signal(
                name=f"Статичный сигнал {i + 1}",
                join_until=current_time + timedelta(seconds=join_time),
                expires_at=current_time + timedelta(seconds=active_time),
                burn_chance=risk,
                profit_percent=profit,
                signal_cost=signal_cost
            )
            db.add(signal)

        await db.commit()

    except Exception as e:
        logging.error(f"Ошибка при создании статичных сигналов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании статичных сигналов: {e}")



async def process_signals(db: AsyncSession):
    now = current_moscow_time()

    try:
        
        # Получаем сигналы, которые еще не были обработаны
        result = await db.execute(
            select(Signal).options(joinedload(Signal.investments))
            .filter(Signal.expires_at <= now, Signal.is_successful.is_(None))
        )
        signals = result.unique().scalars().all()
        

        for signal in signals:
            success = random.random() > BURN_CHANCE
            signal.is_successful = success


            for investment in signal.investments:
                if investment.is_checked:
                    continue

                user_id = investment.user_id
                amount = investment.amount

                # Получаем пользователя для получения информации о его балансе и reinvestments_par
                user_result = await db.execute(select(User).filter(User.id == user_id))
                user = user_result.scalars().first()

                if not user:
                    logging.warning(f"\n\n\n⚠️ Пользователь {user_id} не найден, пропускаем")
                    continue

                profit = round(amount * (PROFIT_PERCENT - 1), 2)  # Округление до 2 знаков
                total_earned = amount + profit
                reinvestment_amount = round((profit * user.reinvestements_par) / 100, 2)  # Округление


                if success:
                    await freeze_balance(db, user_id, total_earned)
                    await update_trading_balance(db, user_id, reinvestment_amount)

                # Запись в Profit
                profit_entry = Profit(
                    user_id=user_id,
                    signal_id=signal.id,
                    amount=amount,  # Записываем исходную сумму
                    profit=profit,  # Прибыль
                    reinvested_amount=reinvestment_amount
                )
                db.add(profit_entry)

                # Записываем успешность сигнала в SignalInvestment
                investment.profit = success  # Устанавливаем успешность инвестиции
                db.add(investment)  # Добавляем инвестицию в транзакцию для коммита

                if user.in_work > 0 and user.in_work <= user.plan:
                    investment.in_work -= 1
                    user.in_work -= 1

                investment.is_checked = True  # Отмечаем инвестицию как проверенную

            # Если сигнал неуспешен, просто записываем False в profit для всех не проверенных инвестиций
            if not success:
                for investment in signal.investments:
                    if not investment.is_checked:
                        investment.profit = False
                        db.add(investment)  # Запись изменений в коммит

        await db.commit()  # Сохраняем изменения в базе данных

        # Перезапускаем создание статичных сигналов после обработки всех сигналов
        await create_static_signals(db)

    except Exception as e:
        logging.error(f"\n\n\n🔥 Ошибка при обработке сигналов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке сигналов: {e}")



async def update_earned_balance(db: AsyncSession, user_id: int, earned_amount: float):
    balance_result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
    balance = balance_result.scalars().first()
    if not balance:
        raise HTTPException(status_code=404, detail="Баланс не найден")
    
    balance.earned_balance += earned_amount
    balance.balance += earned_amount
    await db.commit()
    await process_referral_bonus(db, user_id)

async def process_referral_bonus(db: AsyncSession, user_id: int):
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()
    if not user or not user.referred_by_id:
        return
    
    referrer_id = user.referred_by_id
    balance_result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
    balance = balance_result.scalars().first()
    if not balance:
        return
    
    referral_bonus = balance.earned_balance * 0.01
    if referral_bonus > 0:
        ref_balance_result = await db.execute(select(Balance).filter(Balance.user_id == referrer_id))
        ref_balance = ref_balance_result.scalars().first()
        if ref_balance:
            ref_balance.balance += referral_bonus
            await db.commit()
