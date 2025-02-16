from flask import Flask
from flask_cors import CORS
from config import DevelopmentConfig
from .controllers.chapter_controller import chapter_blueprint
from .controllers.project_controller import project_blueprint
from .controllers.sentence_controller import sentence_blueprint
from .controllers.segment_controller import segment_blueprint
from .controllers.concept_controller import concept_blueprint
from application.controllers.lexical_controller import lexical_blueprint
from .controllers.relational_controller import relational_blueprint
from application.controllers.segment_detail_controller import segment_detail_blueprint
from application.controllers.visualizer_controllers import visualizer_blueprint
from .controllers.construction_controller import construction_blueprint
from .controllers.generation_controller import generation_blueprint
from .extensions import db, ma, jwt, migrate
from .controllers.user_controller import user_blueprint
from .controllers.discourse_controller import discourse_blueprint
from flask_mail import Mail


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)

    # Configurations
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'datadialect3@gmail.com'  
    app.config['MAIL_PASSWORD'] = 'krrx faji mcst eckw'         
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    
    # Initialize extensions
    mail = Mail(app)

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
    app.register_blueprint(segment_blueprint, url_prefix = '/api/segments')
    app.register_blueprint(lexical_blueprint, url_prefix='/api/lexicals')
    app.register_blueprint(relational_blueprint, url_prefix='/api/relations')
    app.register_blueprint(concept_blueprint, url_prefix='/api/concepts')
    app.register_blueprint(segment_detail_blueprint, url_prefix='/api/segment_details')
    app.register_blueprint(construction_blueprint, url_prefix='/api/constructions')
    app.register_blueprint(discourse_blueprint, url_prefix='/api/discourse')
    app.register_blueprint(visualizer_blueprint, url_prefix='/api/visualize')
    app.register_blueprint(generation_blueprint, url_prefix='/api/generate')


    return app
