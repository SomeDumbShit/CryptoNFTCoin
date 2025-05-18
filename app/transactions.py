from datetime import datetime
from .models import Transaction, User
from .economy import get_economy
from .extensions import db

class TransactionType:
    TRANSFER = 'transfer'
    PURCHASE = 'purchase'
    SELL = 'sell'
    REWARD = 'reward'
    BURN = 'burn'
    MINT = 'mint'
    CASE_OPEN = 'case_open'
    AUCTION_BID = 'auction_bid'
    ART_PURCHASE = 'art_purchase'

class TransactionsFee: # в виде долей
    TRANSFER = 0.01
    PURCHASE = 0
    SELL = 0.05
    REWARD = 0
    BURN = 0
    MINT = 0
    CASE_OPEN = 0
    AUCTION_BID = 0.01
    ART_PURCHASE = 0.01


# добавление транзакции в бд
def log_transaction(*, amount, transaction_type, sender_id=None, recipient_id=None, art_id=None, meta=None):
    transaction = Transaction(
        sender_id=sender_id,
        recipient_id=recipient_id,
        amount=amount,
        transaction_type=transaction_type,
        art_id=art_id,
        meta=meta,
        timestamp=datetime.utcnow()
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction


# награда за задание
def reward_user(user_id, amount, metadata=None):
    economy = get_economy()
    economy.mint(amount)
    user = User.query.get(user_id)
    user.balance += amount
    return log_transaction(
        recipient_id=user_id,
        amount=amount,
        transaction_type=TransactionType.REWARD,
        meta=metadata  # список наград
    )


def burn_tokens(user_id, amount, metadata=None):
    economy = get_economy()
    economy.burn(amount)
    user = db.session.query(User).get(user_id)
    user.balance -= amount
    return log_transaction(
        sender_id=user_id,
        amount=amount,
        transaction_type=TransactionType.BURN,
        meta=metadata
    )


def mint_tokens(user_id, amount, metadata=None):
    economy = get_economy()
    economy.mint(amount)
    return log_transaction(
        recipient_id=user_id,
        amount=amount,
        transaction_type=TransactionType.MINT,
        meta=metadata
    )


def transfer_tokens(sender_id, recipient_id, amount, comment=None):
    #======================      переводы валюты (второстепенно)      ===================
    return log_transaction(
        sender_id=sender_id,
        recipient_id=recipient_id,
        amount=amount,
        transaction_type=TransactionType.TRANSFER,
        meta=comment
    )


def purchase(buyer_id, amount, comment=None):
    economy = get_economy()
    user = db.session.query(User).get(buyer_id)
    user.balance += amount
    economy.buy(amount)
    return log_transaction(
        recipient_id=buyer_id,
        amount=amount,
        transaction_type=TransactionType.PURCHASE,
        meta=comment
    )


def sell(seller_id, amount, comment=None):
    economy = get_economy()
    user = db.session.query(User).get(seller_id)
    user.balance -= amount
    economy.sell(amount)
    return log_transaction(
        recipient_id=seller_id,
        amount=amount,
        transaction_type=TransactionType.PURCHASE,
        meta=comment
    )


def art_purchase(buyer_id, seller_id, amount, art_id):
    return log_transaction(
        sender_id=buyer_id,
        recipient_id=seller_id,
        amount=amount,
        transaction_type=TransactionType.ART_PURCHASE,
        art_id=art_id
    )
