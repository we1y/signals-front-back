from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.services.get_db import get_db  # Импортируем get_db
from app.database import get_db as main 
from app.models.models import Profit, Transaction, User, Referrals, Balance  # Убедитесь, что Balance подключена
from sqlalchemy.orm import subqueryload
from app.services.users import add_referral
# Логирование
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

app = FastAPI()

router = APIRouter(prefix="/api")

#-------------------------------------------------------------------------#   

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):  # db - это сессия
    try:
        # Выполняем запрос через сессию db
        result = await db.execute(
            select(User)
            .options(
                subqueryload(User.balance),  # Используем subqueryload для баланса
                subqueryload(User.referred_by)  # Используем subqueryload для реферера
            )
        )
        users = result.scalars().all()  # Получаем список пользователей

        return [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "language_code": u.language_code,
                "is_bot": u.is_bot,
                "photo_url": u.photo_url,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
                "balance": u.balance.balance if u.balance else 0.0,
                "trade_balance": u.balance.trade_balance if u.balance else 0.0,
                "referred_by": {
                    "id": u.referred_by.id if u.referred_by else None,
                    "telegram_id": u.referred_by.telegram_id if u.referred_by else None,
                    "username": u.referred_by.username if u.referred_by else None
                } if u.referred_by else None
            }
            for u in users
        ]
    except Exception as e:
        # Логирование ошибки
        logging.error(f"Ошибка при получении пользователей: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving users.")
    
    #-------------------------------------------------------------------------#   

### 🔹 **Поиск пользователя по telegram_id**
@router.get("/user/{telegram_id}")
async def get_user_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    try:
        logging.info(f"Пытаемся получить пользователя с telegram_id: {telegram_id}")

        # Запрос с загрузкой баланса и реферера
        result = await db.execute(
            select(User)
            .options(
                subqueryload(User.balance),  # Баланс
                subqueryload(User.referred_by)  # Реферер
            )
            .filter(User.telegram_id == telegram_id)
        )
        user = result.scalars().first()

        if user is None:
            logging.warning(f"Пользователь с telegram_id {telegram_id} не найден.")
            raise HTTPException(status_code=404, detail="User not found")


        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_bot": user.is_bot,
            "photo_url": user.photo_url,
            "automod": user.automod,  # Автоматический режим
            "plan": user.plan,  # Тарифный план
            "reinvestements_par": user.reinvestements_par,  # Процент реинвестирования
            "in_work": user.in_work,  # В работе
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "plan": user.plan,
            "balance": {
                "balance": user.balance.balance if user.balance else 0.0,
                "trade_balance": user.balance.trade_balance if user.balance else 0.0,
                "frozen_balance": user.balance.frozen_balance if user.balance else 0.0,
                "earned_balance": user.balance.earned_balance if user.balance else 0.0
            } if user.balance else None,
            "referred_by": {
                "id": user.referred_by.id if user.referred_by else None,
                "telegram_id": user.referred_by.telegram_id if user.referred_by else None,
                "username": user.referred_by.username if user.referred_by else None
            } if user.referred_by else None
        }

    except Exception as e:
        logging.error(f"Ошибка при получении пользователя с telegram_id {telegram_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the user.")
    
#-------------------------------------------------------------------------#   

@router.get("/transactions/{telegram_id}")
async def get_transactions(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """ Получает список транзакций пользователя по telegram_id. """
    try:
        user_result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user_result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        transactions_result = await db.execute(
            select(Transaction).filter(Transaction.user_id == user.id)
        )
        transactions = transactions_result.scalars().all()

        return [{
            "id": transaction.id,
            "amount": transaction.amount,
            "transaction_type": transaction.transaction_type,
            "created_at": transaction.created_at
        } for transaction in transactions]
    except Exception as e:
        logging.error(f"Error retrieving transactions for telegram_id {telegram_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving transactions.")
    
#-------------------------------------------------------------------------#   

@router.get("/profits/{telegram_id}")
async def get_profits(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """ Получает список прибыли пользователя по telegram_id. """
    try:
        user_result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = user_result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        profits_result = await db.execute(
            select(Profit).filter(Profit.user_id == user.id)
        )
        profits = profits_result.scalars().all()

        return [{
            "id": profit.id,
            "amount": profit.amount,
            "signal_id": profit.signal_id,
            "created_at": profit.created_at
        } for profit in profits]
    except Exception as e:
        logging.error(f"Error retrieving profits for telegram_id {telegram_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving profits.")
    
#-------------------------------------------------------------------------#   

class ReferralRequest(BaseModel):
    telegram_id: int
    referral_link: str

@router.post("/check_referral")
async def check_referral(request: ReferralRequest, db: AsyncSession = Depends(get_db)):
    """ 
    Привязывает пользователя к владельцу реферальной ссылки,
    записывая его telegram_id в поле referred_by.
    """
    # Ищем владельца реферальной ссылки
    referrer_result = await db.execute(
        select(Referrals).filter(Referrals.referral_link == request.referral_link)
    )
    referrer = referrer_result.scalars().first()

    if not referrer:
        return {"exists": False, "message": "Реферальная ссылка не найдена"}

    # Ищем приглашённого пользователя по его telegram_id
    result = await db.execute(
        select(Referrals).filter(Referrals.telegram_id == request.telegram_id)
    )
    referral = result.scalars().first()

    if referral:
        # Если пользователь уже привязан, ничего не меняем
        if referral.referred_by:
            return {
                "exists": True,
                "message": "Пользователь уже привязан",
                "referral_data": {
                    "telegram_id": referral.telegram_id,
                    "referred_by": referral.referred_by
                }
            }
        # Записываем telegram_id владельца ссылки в referred_by
        referral.referred_by = referrer.telegram_id
        referrer.invited_count += 1  # Увеличиваем счётчик приглашённых

        # Сохраняем изменения в БД
        await db.commit()

        return {
            "exists": True,
            "message": "Пользователь успешно привязан",
            "referral_data": {
                "telegram_id": referral.telegram_id,
                "referred_by": referral.referred_by
            }
        }

    return {"exists": False, "message": "Пользователь не найден"}

#-------------------------------------------------------------------------#   

@router.put("/user/{telegram_id}/update_plan")
async def update_user_plan(telegram_id: int, new_plan: int, db: AsyncSession = Depends(get_db)):
    """
    Обновляет план пользователя (plan) на одно из значений: 0, 1 или 2.
    """
    allowed_plans = {0, 1, 2}

    if new_plan not in allowed_plans:
        raise HTTPException(status_code=400, detail="Invalid plan value. Allowed values: 0, 1, 2")

    try:
        # Ищем пользователя по telegram_id
        result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if not user:
            logging.warning(f"Пользователь с telegram_id {telegram_id} не найден.")
            raise HTTPException(status_code=404, detail="User not found")

        # Обновляем значение plan
        user.plan = new_plan
        await db.commit()
        await db.refresh(user)

        logging.info(f"Обновлен план пользователя {telegram_id} до {new_plan}")
        return {"message": "User plan updated successfully", "telegram_id": telegram_id, "new_plan": new_plan}

    except HTTPException:
        raise  # Оставляем 404 без изменений

    except Exception as e:
        logging.error(f"Ошибка при обновлении плана пользователя {telegram_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

#-------------------------------------------------------------------------#  

@router.get("/referral_tree/{telegram_id}")
async def get_referral_tree(telegram_id: str, db: AsyncSession = Depends(get_db)):
    async def fetch_referrals(telegram_id):
        """Рекурсивно получаем всех приглашённых пользователей по их Telegram ID"""
        logging.info(f"Fetching referrals for telegram_id: {telegram_id}")  

        result = await db.execute(
            select(Referrals).filter(Referrals.referred_by == telegram_id)  # Ищем рефералов по telegram_id
        )
        referrals = result.scalars().all()

        logging.info(f"Found {len(referrals)} referrals for telegram_id: {telegram_id}")  

        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "telegram_id": r.telegram_id,
                "referral_link": r.referral_link,
                "invited_count": r.invited_count,
                "referrer_id": r.referrer_id,
                "referred_by": r.referred_by,
                "invited_users": await fetch_referrals(r.telegram_id)  # Рекурсивно получаем рефералов
            }
            for r in referrals
        ]

    try:
        logging.info(f"Received request to fetch referral tree for telegram_id: {telegram_id}")  

        # Приводим telegram_id к int
        telegram_id = int(telegram_id)

        # Ищем пользователя по его telegram_id
        result = await db.execute(
            select(Referrals).filter(Referrals.telegram_id == telegram_id)
        )
        user = result.scalars().first()

        if not user:
            logging.warning(f"User not found for telegram_id: {telegram_id}")  
            raise HTTPException(status_code=404, detail="User not found")

        logging.info(f"Found user: {user.user_id} with telegram_id: {telegram_id}")  

        # Получаем всех приглашённых пользователей (рефералов)
        referral_tree = {
            "id": user.id,
            "user_id": user.user_id,
            "telegram_id": user.telegram_id,
            "referral_link": user.referral_link,
            "invited_count": user.invited_count,
            "referrer_id": user.referrer_id,
            "referred_by": user.referred_by,
            "invited_users": await fetch_referrals(user.telegram_id)  # Исправленный вызов
        }

        logging.info(f"Referral tree successfully retrieved for telegram_id: {telegram_id}")  

        return referral_tree

    except Exception as e:
        logging.error(f"Error retrieving referral tree for telegram_id: {telegram_id}: {e}", exc_info=True)  
        raise HTTPException(status_code=500, detail="An error occurred while retrieving referral tree.")