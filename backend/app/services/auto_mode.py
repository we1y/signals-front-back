from datetime import datetime, timezone, timedelta
import random
from sqlalchemy.future import select
from app.models.models import User, Signal, SignalInvestment, Balance

async def process_auto_mode_users(db):
    """Обрабатывает пользователей с включенным автомодом, автоматически подключая их к сигналам"""
    now = datetime.now(timezone.utc)

    # 1️⃣ Получаем всех пользователей, у которых включен автомод
    result = await db.execute(select(User).filter(User.auto_mode_enabled == True))
    auto_users = result.scalars().all()

    for user in auto_users:
        # 2️⃣ Получаем баланс пользователя
        balance_result = await db.execute(select(Balance).filter(Balance.user_id == user.id))
        balance = balance_result.scalars().first()

        if not balance or balance.balance < 10:  # Проверка минимального баланса
            print(f"⛔ Пользователь {user.id} не может участвовать - недостаточно средств!")
            continue

        # 3️⃣ Ищем активный сигнал
        signal_result = await db.execute(select(Signal).filter(Signal.expires_at > now))
        signal = signal_result.scalars().first()

        # 4️⃣ Если активного сигнала нет — создаём новый
        if not signal:
            # Создаем авто-сигнал с случайными параметрами или заданными для автоматического режима
            burn_chance = random.uniform(1, 5)  # случайный шанс сгорания от 1 до 5%
            profit_percent = random.uniform(5, 15)  # случайный процент прибыли от 5 до 15%
            signal_cost = random.randint(100, 200)  # случайная стоимость входа

            signal = Signal(
                name="Автоматический сигнал",
                join_until=now + timedelta(minutes=5),  # Время на вход в сигнал
                expires_at=now + timedelta(hours=1),  # Сигнал активен 1 час
                is_successful=None,
                burn_chance=burn_chance,  # случайный шанс сгорания
                profit_percent=profit_percent,  # случайный процент прибыли
                signal_cost=signal_cost  # случайная цена входа
            )
            db.add(signal)
            await db.commit()  # Асинхронно коммитим

            print(f"🚀 Новый авто-сигнал создан с параметрами: {signal.name}, шанс сгорания: {burn_chance}%, процент прибыли: {profit_percent}%, цена: {signal_cost}")

        # 5️⃣ Проверяем, что пользователь уже не участвует в сигнале
        investment_result = await db.execute(
            select(SignalInvestment).filter(
                SignalInvestment.user_id == user.id,
                SignalInvestment.signal_id == signal.id
            )
        )
        existing_investment = investment_result.scalars().first()

        if existing_investment:
            print(f"✅ Пользователь {user.id} уже участвует в сигнале {signal.id}")
            continue

        # 6️⃣ Создаём инвестицию
        investment = SignalInvestment(
            user_id=user.id,
            signal_id=signal.id,
            amount=signal.signal_cost,
            auto_mode=True
        )
        balance.balance -= signal.signal_cost  # Списываем деньги с баланса

        db.add(investment)
        await db.commit()  # Асинхронно коммитим
        print(f"🚀 Пользователь {user.id} подключен к сигналу {signal.id} с автоматическим режимом")
