from flask import Flask
from flask_cors import CORS
from config import DevelopmentConfig
from application.controllers.chapter_controller import chapter_blueprint
from application.controllers.project_controller import project_blueprint
from application.controllers.sentence_controller import sentence_blueprint
from application.controllers.segment_controller import segment_blueprint
from application.controllers.concept_controller import concept_blueprint
from application.controllers.lexical_controller import lexical_blueprint
from application.controllers.relational_controller import relational_blueprint
from application.controllers.segment_detail_controller import segment_detail_blueprint
from application.controllers.visualizer_controllers import visualizer_blueprint
from application.controllers.construction_controller import construction_blueprint
from application.controllers.generation_controller import generation_blueprint
from application.controllers.user_controller import user_blueprint
from application.controllers.discourse_controller import discourse_blueprint
from application.controllers.assignment_controllers import assignment_blueprint
from application.controllers.notification_controller import notification_blueprint
from application.controllers.reviewer_controller import reviewer_blueprint
from flask_mail import Mail
from application.extensions import db, ma, jwt, migrate, mail
import secrets

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)
    
    # Double-check SECRET_KEY is set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        print("WARNING: Generated temporary SECRET_KEY. Please set SECRET_KEY in your config.py or environment variables.")
    else:
        print(f"Using SECRET_KEY: {app.config['SECRET_KEY'][:5]}... (first 5 chars)")

    # Initialize extensions
    mail.init_app(app)
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Enable CORS
    CORS(app)

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(user_blueprint, url_prefix='/api/users')
    app.register_blueprint(project_blueprint, url_prefix='/api/projects')
    app.register_blueprint(chapter_blueprint, url_prefix='/api/chapters')
    app.register_blueprint(sentence_blueprint, url_prefix='/api/sentences')
    app.register_blueprint(segment_blueprint, url_prefix='/api/segments')
    app.register_blueprint(lexical_blueprint, url_prefix='/api/lexicals')
    app.register_blueprint(relational_blueprint, url_prefix='/api/relations')
    app.register_blueprint(concept_blueprint, url_prefix='/api/concepts')
    app.register_blueprint(segment_detail_blueprint, url_prefix='/api/segment_details')
    app.register_blueprint(construction_blueprint, url_prefix='/api/constructions')
    app.register_blueprint(discourse_blueprint, url_prefix='/api/discourse')
    app.register_blueprint(visualizer_blueprint, url_prefix='/api/visualize')
    app.register_blueprint(generation_blueprint, url_prefix='/api/generate')
    app.register_blueprint(assignment_blueprint, url_prefix='/api/assignments')
    app.register_blueprint(notification_blueprint, url_prefix='/api/notifications')
    app.register_blueprint(reviewer_blueprint, url_prefix='/api/review')

    return app