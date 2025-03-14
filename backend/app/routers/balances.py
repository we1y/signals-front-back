import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.services.get_db import get_db  # Импортируем get_db
from app.models.models import Referrals, User, Balance 
from app.services.balances import (
    has_sufficient_trading_balance,
    update_balance, 
    has_sufficient_balance,
    get_balance,
    update_referral_by_url,
    update_trading_balance,
    freeze_balance,  # 🔹 Функция заморозки
    unfreeze_balance  # 🔹 Функция разблокировки
)
#-------------------------------------------------------------------------#   
router = APIRouter(prefix="/api")

class AmountRequest(BaseModel):
    amount: float

class ReferralRequest(BaseModel):
    telegram_id: int
    referral_link: str

logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

#-------------------------------------------------------------------------#   

@router.get("/balance/{telegram_id}")
async def get_balance_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(joinedload(User.balance)).filter(User.telegram_id == telegram_id)
    )
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "balance": user.balance.balance if user.balance else 0.0,
        "trade_balance": user.balance.trade_balance if user.balance else 0.0,
        "frozen_balance": user.balance.frozen_balance if user.balance else 0.0
    }

#-------------------------------------------------------------------------#   

@router.post("/transfer_to_trading/{telegram_id}")
async def transfer_to_trading(telegram_id: int, request: AmountRequest, db: AsyncSession = Depends(get_db)):
    amount = request.amount

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if await has_sufficient_balance(db, user.id, amount):
        if await update_balance(db, user.id, -amount):
            if await update_trading_balance(db, user.id, amount):
                await freeze_balance(db, user.id, amount)
                return {"message": "Transfer successful, funds frozen"}

    raise HTTPException(status_code=400, detail="Insufficient balance")

#-------------------------------------------------------------------------#   

@router.get("/unfreeze_balance/{telegram_id}")
async def unfreeze(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    balance_result = await db.execute(select(Balance).filter(Balance.user_id == user.id))
    balance = balance_result.scalars().first()

    if not balance or balance.frozen_balance <= 0:
        raise HTTPException(status_code=400, detail="No frozen balance to unfreeze")

    amount_to_unfreeze = balance.frozen_balance
    balance.trade_balance += amount_to_unfreeze
    balance.frozen_balance = 0

    await db.commit()

    return {
        "message": "Balance unfrozen",
        "unfrozen_amount": amount_to_unfreeze,
        "new_trade_balance": balance.trade_balance
    }

#-------------------------------------------------------------------------#   

@router.post("/deposit/{telegram_id}")
async def deposit(telegram_id: int, request: AmountRequest, db: AsyncSession = Depends(get_db)):
    amount = request.amount
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    balance = await get_balance(db, user.id)
    if balance is None:
        raise HTTPException(status_code=404, detail="Balance not found")

    success = await update_balance(db, user.id, amount)

    if success:
        updated_balance = await get_balance(db, user.id)
        return {"message": "Deposit successful", "new_balance": updated_balance.balance}

    raise HTTPException(status_code=500, detail="Failed to update balance")

#-------------------------------------------------------------------------#   

@router.post("/transfer_to_main/{telegram_id}")
async def transfer_to_main(telegram_id: int, request: AmountRequest, db: AsyncSession = Depends(get_db)):
    amount = request.amount

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if await has_sufficient_trading_balance(db, user.id, amount):
        if await update_trading_balance(db, user.id, -amount):
            if await update_balance(db, user.id, amount):
                result = await db.execute(
                    select(User).options(joinedload(User.balance)).filter(User.telegram_id == telegram_id)
                )
                user = result.scalars().first()

                if user is None:
                    raise HTTPException(status_code=404, detail="User not found")

                return {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "balance": user.balance.balance if user.balance else 0.0,
                    "trade_balance": user.balance.trade_balance if user.balance else 0.0,
                    "frozen_balance": user.balance.frozen_balance if user.balance else 0.0
                }

    raise HTTPException(status_code=400, detail="Insufficient trading balance")

#-------------------------------------------------------------------------#   