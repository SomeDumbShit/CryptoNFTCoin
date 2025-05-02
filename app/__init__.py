from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager

from .extensions import db
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Sdsoff'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nftmarket.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # блупринт
    from .routes import main
    from .auth_routes import auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    from .models import User, Art, Auction, Quest, UserQuest, Transaction

    # создание заранее табл
    with app.app_context():
        db.create_all()

    return app

