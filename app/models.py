from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import JSON

from .extensions import db


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')
    avatar = db.Column(db.String(255), default='uploads/avatars/default.png')
    attributes = db.Column(JSON, default={'background': ['green'], 'body': ['panda'], 'eyes': ['angry_eyes'],
                                            'ears': ['black_ears'], 'mouth': ['joyful'], 'clothes': ['none', 'blaze'],
                                            'hats': ['none'], 'accessory': ['none']})
    arts = db.relationship(
        'Art',
        backref='owner',
        lazy=True,
        foreign_keys='Art.owner_id'
    )

    arts_created = db.relationship(
        'Art',
        backref='artist',
        lazy=True,
        foreign_keys='Art.artist_id'
    )

    transactions_sent = db.relationship(
        'Transaction',
        foreign_keys='Transaction.sender_id',
        backref='sender',
        lazy=True
    )

    transactions_received = db.relationship(
        'Transaction',
        foreign_keys='Transaction.recipient_id',
        backref='recipient',
        lazy=True
    )



class Art(db.Model):
    __tablename__ = 'art'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='available')
    art_metadata = db.Column(db.String, nullable=False)
    transactions = db.relationship('Transaction', backref='art_ref', lazy=True)
    price = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    auctions = db.relationship('Auction', backref='art', lazy=True)
    description = db.Column(db.Text)
    moderation_status = db.Column(db.String(20), default='pending')
    rarity = db.Column(db.String(20), default='common')



class Auction(db.Model):
    __tablename__ = 'auction'
    id = db.Column(db.Integer, primary_key=True)
    art_id = db.Column(db.Integer, db.ForeignKey('art.id'), nullable=False)
    current_bid = db.Column(db.Integer, default=0)
    last_bidder_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    end_time = db.Column(db.DateTime, nullable=False)


class Quest(db.Model):
    __tablename__ = 'quest'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(100), nullable=False)


class UserQuest(db.Model):
    __tablename__ = 'user_quest'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)
    status = db.Column(db.String(20), default='in_progress')  # может быть 'in_progress', 'completed'


class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    transaction_fee = db.Column(db.Integer, nullable=True)
    art_id = db.Column(db.Integer, db.ForeignKey('art.id'), nullable=True)
    transaction_type = db.Column(db.String(50), nullable=False)  # все возможные типы в transactions.TransactionType
    meta = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Economy(db.Model):
    __tablename__ = 'economy'
    id = db.Column(db.Integer, primary_key=True)
    total_supply = db.Column(db.Integer, default=0)  # выпущено токенов
    circulating_supply = db.Column(db.Integer, default=0)  # оборот токенов (выпущено - сожжено)
    burned = db.Column(db.Integer, default=0)  # сожжено токенов
    base_price = db.Column(db.Integer, default=0.1)  # минимальная цена
    price = db.Column(db.Integer, default=0.1)  # текущая цена
    growth_factor = db.Column(db.Integer, default=10)  # коэффициент волатильности
    last_updated = db.Column(db.Integer, default=datetime.utcnow)
    max_supply = db.Column(db.Integer, default=1_000_000)  # предел количества токенов
    market_cap = db.Column(db.Integer, default=0)  # капитализация
