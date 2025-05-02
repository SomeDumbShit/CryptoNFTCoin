from app import create_app
from .extensions import db

app = create_app()
with app.app_context():
    from .models import User, Art, Auction, Quest, UserQuest, Transaction
    db.create_all()
