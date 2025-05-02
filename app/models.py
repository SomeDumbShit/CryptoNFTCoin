
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')  # может быть 'user', 'artist', 'admin'

    arts = db.relationship('Art', backref='owner', lazy=True)
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
    image_path = db.Column(db.String(120), nullable=False)
    art_metadata = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='available')  # состояние картины 'available', 'sold', 'auction'

    auctions = db.relationship('Auction', backref='art', lazy=True)

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
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    art_id = db.Column(db.Integer, db.ForeignKey('art.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_type = db.Column(db.String(50))  # транкзация может быть 'purchase', 'auction', 'reward'
