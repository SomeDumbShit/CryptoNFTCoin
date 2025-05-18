import os

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from .extensions import db

migrate = Migrate()
login_manager = LoginManager()
basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Sdsoff'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nftmarket.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')

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

    from .models import User, Art, Auction, Quest, UserQuest, Transaction, Economy

    # создание заранее табл и загрузка данных экономики
    with app.app_context():
        db.create_all()

    return app

