from flask import Flask
from flask_cors import CORS
from config import DevelopmentConfig
from .controllers.chapter_controller import chapter_blueprint
from .controllers.project_controller import project_blueprint
from .controllers.sentence_controller import sentence_blueprint
from .extensions import db, ma, jwt, migrate
from .controllers.user_controller import user_blueprint


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    CORS(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(user_blueprint, url_prefix='/api/users')
    app.register_blueprint(project_blueprint, url_prefix='/api/projects')
    app.register_blueprint(chapter_blueprint, url_prefix='/api/chapters')
    app.register_blueprint(sentence_blueprint, url_prefix='/api/sentences')


    return app
