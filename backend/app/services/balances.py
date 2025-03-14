import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.models import Balance, Referrals
from app.statistics_services.balance_actions import log_transaction
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

async def get_balance(db: AsyncSession, user_id: int) -> Balance:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        return result.scalars().first()
    except SQLAlchemyError as e:
        logging.error(f"Ошибка получения баланса пользователя {user_id}: {e}")
        return None

async def create_or_update_balance(db: AsyncSession, user_id: int, balance: float, trade_balance: float, frozen_balance: float = 0.0) -> Balance:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        user_balance = result.scalars().first()

        if user_balance is None:
            user_balance = Balance(user_id=user_id, balance=balance, trade_balance=trade_balance, frozen_balance=frozen_balance)
            db.add(user_balance)
        else:
            user_balance.balance = balance
            user_balance.trade_balance = trade_balance
            user_balance.frozen_balance = frozen_balance

        await db.commit()
        await db.refresh(user_balance)
        return user_balance
    except SQLAlchemyError as e:
        logging.error(f"Ошибка обновления баланса {user_id}: {e}")
        await db.rollback()
        return None

async def update_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        balance = result.scalars().first()

        if balance:
            balance.balance += amount
            await db.commit()
            await db.refresh(balance)
            await log_transaction(db, user_id, amount, "balance_update")
            return True
        return False
    except SQLAlchemyError as e:
        logging.error(f"Ошибка обновления баланса {user_id}: {e}")
        await db.rollback()
        return False

async def update_trading_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        balance = result.scalars().first()

        if balance:
            balance.trade_balance += amount
            await db.commit()
            await db.refresh(balance)
            await log_transaction(db, user_id, amount, "trade_balance_update")
            return True
        return False
    except SQLAlchemyError as e:
        logging.error(f"Ошибка обновления торгового баланса {user_id}: {e}")
        await db.rollback()
        return False

async def freeze_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        balance = result.scalars().first()

        if balance and balance.balance >= amount:
            balance.balance -= amount
            balance.frozen_balance += amount
            await db.commit()
            await db.refresh(balance)
            await log_transaction(db, user_id, amount, "freeze")
            return True
        return False
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при заморозке баланса {user_id}: {e}")
        await db.rollback()
        return False

async def unfreeze_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        balance = result.scalars().first()

        if balance and balance.frozen_balance >= amount:
            balance.frozen_balance -= amount
            balance.balance += amount
            await db.commit()
            await db.refresh(balance)
            await log_transaction(db, user_id, amount, "unfreeze")
            return True
        return False
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при разморозке баланса {user_id}: {e}")
        await db.rollback()
        return False

async def has_sufficient_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        balance = result.scalars().first()
        return balance and balance.balance >= amount
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при проверке баланса {user_id}: {e}")
        return False

async def has_sufficient_trading_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
    try:
        result = await db.execute(select(Balance).filter(Balance.user_id == user_id))
        balance = result.scalars().first()
        return balance and balance.trade_balance >= amount
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при проверке торгового баланса {user_id}: {e}")
        return False

async def update_referral_by_url(referral_by_telegram: Referrals, referral_by_link: Referrals) -> bool:
    try:
        async with get_db() as db:
            telegram_id = referral_by_telegram.telegram_id
            referral_link = referral_by_link.referral_link
            
            if isinstance(referral_link, str):
                referral_parts = referral_link.split("/")[-1].split("-")
                if len(referral_parts) != 2:
                    return False
                link_telegram_id = int(referral_parts[1])
            else:
                return False

            result = await db.execute(select(Referrals).filter(Referrals.telegram_id == link_telegram_id))
            referral_owner = result.scalars().first()

            if not referral_owner:
                return False

            referral_owner = await db.merge(referral_owner)
            referral_by_telegram = await db.merge(referral_by_telegram)

            referral_owner.invited_count += 1
            referral_by_telegram.referred_by = link_telegram_id

            await db.commit()
            await db.refresh(referral_by_telegram)
            await db.refresh(referral_owner)
            return True
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при обновлении данных для telegram_id {referral_by_telegram.telegram_id}: {e}")
        if db:
            await db.rollback()
        return False
