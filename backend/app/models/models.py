from sqlalchemy import Column, Double, Integer, Float, ForeignKey, Numeric, String, Boolean, TIMESTAMP, BigInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
Base = declarative_base()



class AuthTokens(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False)  # Обновили на telegram_id
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Связь с пользователем через telegram_id
    user = relationship("User", back_populates="auth_tokens")

    def __repr__(self):
        return f"<AuthTokens(token={self.token}, user_telegram_id={self.user_id}, expires_at={self.expires_at})>"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language_code = Column(String(10))
    is_bot = Column(Boolean, default=False)
    photo_url = Column(String(255))
    automod = Column(Boolean, default=False)  # Новый столбец
    plan = Column(Integer, default=0)  # Новый столбец
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    reinvestements_par = Column(Integer, default=0)
    in_work = Column(Integer, nullable=False)

    # ➕ Новые поля для автомода
    auto_mode_enabled = Column(Boolean, default=False)  # Автоматический режим включен?
    auto_mode_last_checked = Column(DateTime(timezone=True), nullable=True)  # Последняя проверка автомода
    auto_mode_locked_until = Column(DateTime(timezone=True), nullable=True)  # Блокировка отключения (на 1 день)

    # Связи с другими таблицами
    balance = relationship("Balance", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    referrals = relationship("Referrals", back_populates="user", foreign_keys="[Referrals.user_id]")
    referred_by = relationship("Referrals", back_populates="referrer", foreign_keys="[Referrals.referrer_id]")
    investments = relationship("SignalInvestment", back_populates="user")
    profits = relationship("Profit", back_populates="user")
    auth_tokens = relationship("AuthTokens", back_populates="user")  # Добавляем связь с токенами



class Balance(Base):
    __tablename__ = 'balances'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    balance = Column(Float, default=0.0)  # Основной баланс
    trade_balance = Column(Float, default=0.0)  # Торговый баланс
    frozen_balance = Column(Float, default=0.0)  # Замороженные средства
    earned_balance = Column(Float, default=0.0)  # ✅ Новый столбец для хранения чистой прибыли
    user = relationship("User", back_populates="balance")



class Referrals(Base):
    __tablename__ = 'referrals'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    referral_link = Column(String, nullable=False)
    invited_count = Column(Integer, default=0)
    referrer_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=True)
    referred_by = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    # Связь с пользователем (тот, кто был приглашен)
    user = relationship("User", foreign_keys=[user_id], back_populates="referrals")
    
    # Связь с пользователем (реферер)
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referred_by")


class Signal(Base):
    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    join_until = Column(DateTime(timezone=True))  # ✅ Добавлено timezone=True
    expires_at = Column(DateTime(timezone=True))  # ✅ Добавлено timezone=True
    is_successful = Column(Boolean, nullable=True)
    burn_chance = Column(Float, nullable=False)
    profit_percent = Column(Float, nullable=False)
    investments = relationship("SignalInvestment", back_populates="signal")
    signal_cost = Column(Integer, nullable=False)
    success_profit_multiplier = Column(Float, nullable=False, default=1.01)  # ✅ Новый столбец

class SignalInvestment(Base):
    __tablename__ = 'signal_investments'

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Float, nullable=False)  
    profit = Column(Boolean, nullable=True)  
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())  # ✅ Добавлено timezone=True
    is_checked = Column(Boolean, default=False, nullable=False)  # Новый флаг

    # ➕ Новый флаг, указывает, что это инвестиция автомода
    auto_mode = Column(Boolean, default=False, nullable=False)

    signal = relationship("Signal", back_populates="investments")
    user = relationship("User", back_populates="investments")


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)  
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())  # ✅ Добавлено timezone=True
    user = relationship("User", back_populates="transactions")


class Profit(Base):
    __tablename__ = 'profits'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    signal_id = Column(Integer, ForeignKey('signals.id', ondelete='CASCADE'), nullable=True)  
    profit = Column(Numeric(precision=16, scale=2), nullable=True)  # Пример исправления для числового поля
    amount = Column(Numeric(precision=16, scale=2), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    reinvested_amount = Column(Double, nullable=False, default=0.0)  
    user = relationship("User", back_populates="profits")
