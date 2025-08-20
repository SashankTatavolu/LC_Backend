from application.extensions import db

class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    tab_name = db.Column(db.String(50), nullable=False)  # e.g., 'lexical_conceptual', 'construction'
    chapter_id = db.Column(db.Integer, nullable=False)
    assigned_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    user = db.relationship('User', backref=db.backref('assignments', lazy=True))
    segment = db.relationship('Segment', backref=db.backref('assignments', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'segment_id': self.segment_id,
            'username': self.user.username if self.user else None,  # Add username
            'tab_name': self.tab_name,
            'assigned_at': self.assigned_at
        }


from application.extensions import db
import datetime


class Chapter(db.Model):
    __tablename__ = 'chapters'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = db.relationship('Project', backref=db.backref('chapters', lazy=True))
    uploaded_by = db.relationship('User', backref=db.backref('chapters', lazy=True))
    assigned_users = db.relationship('User', secondary='project_user', backref=db.backref('chapters_assigned', lazy='dynamic'))
    generations = db.relationship('Generation', back_populates='chapter')
    

from application.extensions import db

class ConceptDictionary(db.Model):
    __tablename__ = 'concept_dictionary'

    concept_id = db.Column(db.Integer, primary_key=True)
    concept_label = db.Column (db.String(255), nullable= False)
    hindi_label = db.Column(db.String(255), nullable=False)
    sanskrit_label = db.Column(db.String(255), nullable=True)
    english_label = db.Column(db.String(255), nullable=False)
    mrsc =db.Column(db.String(255), nullable=True)
    

from application.extensions import db

class Construction(db.Model):
    __tablename__ = 'construction'
    construction_id = db.Column(db.Integer, primary_key=True)
    # segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id', ondelete='CASCADE'), nullable=False)
    segment_index = db.Column(db.String(50), nullable=False)
    index = db.Column(db.Integer) 
    construction = db.Column(db.String(50), nullable=False)
    cxn_index = db.Column(db.String(50), nullable=False)
    component_type = db.Column(db.String(255), nullable=False)
    concept_id = db.Column(db.Integer, db.ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)
    isFinalized = db.Column(db.Boolean, default=False, nullable=False) 
    
    segment = db.relationship('Segment', back_populates='construction')
    concept = db.relationship('LexicalConceptual', back_populates='constructions')
    
    def serialize(self):
        return {
            'construction_id': self.construction_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index,
            'construction': self.construction,
            'cxn_index': self.cxn_index,
            'component_type': self.component_type,
            'concept_id': self.concept_id,
            'isFinalized': self.isFinalized
        }


from application.extensions import db

class Discourse(db.Model):
    __tablename__ = 'discourse'
    discourse_id = db.Column(db.Integer, primary_key=True)
    # segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id', ondelete='CASCADE'), nullable=False)
    segment_index = db.Column(db.String(250), nullable=False)
    discourse = db.Column(db.String(250))
    index = db.Column(db.Integer, nullable=False)  # Added index column
    head_index = db.Column(db.String(250), nullable=True)  # Updated head_index to be a string
    relation = db.Column(db.String(255), nullable=True)  # Added relation column
    isFinalized = db.Column(db.Boolean, default=False, nullable=False) 

    segment = db.relationship('Segment', back_populates='discourse')
    concept_id = db.Column(db.Integer, db.ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True) 
    concept = db.relationship('LexicalConceptual', back_populates='discourse')

    def serialize(self):
        return {
            'discourse_id': self.discourse_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index, 
            'head_index': self.head_index,
            'relation': self.relation,
            'concept_id': self.concept_id, 
            'discourse': self.discourse,
            'isFinalized': self.isFinalized
        }

from application.extensions import db
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.models.segment_model import Segment
from application.services.measure_time import measure_response_time

segment_blueprint = Blueprint('segments', __name__)

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    concept_index = db.Column(db.Integer, nullable=True)  
    user_id = db.Column(db.Integer, nullable=False)
    has_error = db.Column(db.Boolean, nullable=False, default=False)
    error_details = db.Column(db.Text)
    tab_name = db.Column(db.String(50), nullable=False, default='lexico_conceptual')  # New column
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def serialize(self):
        return {
            'id': self.id,
            'segment_id': self.segment_id,
            'concept_index': self.concept_index, 
            'user_id': self.user_id,
            'has_error': self.has_error,
            'error_details': self.error_details,
            'tab_name': self.tab_name,
            'timestamp': self.timestamp,
        }



from application.extensions import db

class LexicalConceptual(db.Model):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = db.Column(db.Integer, primary_key=True)
    # segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id', ondelete='CASCADE'), nullable=False)
    segment_index = db.Column(db.String(50), nullable=False)
    index = db.Column(db.Integer)
    concept = db.Column(db.String(255), nullable=False)
    semantic_category = db.Column(db.String(255))
    morpho_semantics = db.Column(db.String(255))
    speakers_view = db.Column(db.String(255))
    isFinalized = db.Column(db.Boolean, default=False, nullable=False)  # <-- New Column
    
    segment = db.relationship('Segment', back_populates='lexical_concepts')
    relational = db.relationship('Relational', back_populates='concept')
    constructions = db.relationship('Construction', back_populates='concept')
    discourse = db.relationship('Discourse', back_populates='concept')
    
    def serialize(self):
        return {
            'lexical_conceptual_id': self.lexical_conceptual_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index,
            'concept': self.concept,
            'semantic_category': self.semantic_category,
            'morpho_semantics': self.morpho_semantics,
            'speakers_view': self.speakers_view,
            'isFinalized': self.isFinalized 
        }



from application.extensions import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # New: Sender
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy=True))
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_notifications', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender_id': self.sender_id,
            'segment_id': self.segment_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at
        }


from application.extensions import db
import datetime

project_user = db.Table('project_user',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('chapter_id', db.Integer, db.ForeignKey('chapters.id'), primary_key=True)
)

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    users = db.relationship('User', secondary=project_user, backref=db.backref('projects', lazy='dynamic'))


from application.extensions import db

class Relational(db.Model):
    __tablename__ = 'relational'
    relational_id = db.Column(db.Integer, primary_key=True)
    # segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id', ondelete='CASCADE'), nullable=False)
    segment_index = db.Column(db.String(50), nullable=False)
    index = db.Column(db.Integer)  # Added index column
    # cxn_index = db.Column(db.Integer)  # Commented out as per your schema update
    head_relation = db.Column(db.String(255), nullable=False)
    head_index = db.Column(db.String(255))  # Added main_index column
    dep_relation = db.Column(db.String(255))  # Added relation column
    is_main = db.Column(db.Boolean, default=False)
    concept_id = db.Column(db.Integer, db.ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)  # Added concept_id column
    isFinalized = db.Column(db.Boolean, default=False, nullable=False) 

    segment = db.relationship('Segment', back_populates='relational')
    concept = db.relationship('LexicalConceptual', back_populates='relational')

    def serialize(self):
        return {
            'relational_id': self.relational_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index,  # Added index field in the serialize method
            # 'cxn_index': self.cxn_index,  # Commented out as per your schema update
            'head_relation': self.head_relation,
            'concept_id': self.concept_id , # Added concept_id in the serialize method
            'head_index': self.head_index,
            'dep_relation': self.dep_relation,
            'isFinalized': self.isFinalized
        }



from application.extensions import db

class Segment(db.Model):
    __tablename__ = 'segments'

    segment_id = db.Column(db.Integer, primary_key=True)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentences.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)  # Add chapter_id
    segment_index = db.Column(db.String(50))
    segment_text = db.Column(db.Text, nullable=False)
    english_text = db.Column(db.Text, nullable=False)  # English text column
    wx_text = db.Column(db.Text, nullable=False)
    segment_type = db.Column(db.String(50))
    index_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')

    # Relationships
    sentence = db.relationship('Sentence', backref=db.backref('segments', lazy=True))
    chapter = db.relationship('Chapter', backref=db.backref('segments', lazy=True))  # Add relationship to Chapter

    lexical_concepts = db.relationship('LexicalConceptual', back_populates='segment')
    relational = db.relationship('Relational', back_populates='segment')
    discourse = db.relationship('Discourse', back_populates='segment')
    construction = db.relationship('Construction', back_populates='segment')
    generations = db.relationship("Generation", back_populates="segment")

    # Serialization
    def serialize(self):
        return {
            'segment_id': self.segment_id,
            'sentence_id': self.sentence_id,
            'chapter_id': self.chapter_id,  # Include chapter_id in serialization
            'segment_index': self.segment_index,
            'segment_text': self.segment_text,
            'english_text': self.english_text,
            'wx_text': self.wx_text,
            'segment_type': self.segment_type,
            'index_type': self.index_type,
            'status': self.status
        }

    def serialize(self, exclude_keys=None):
        data = {
            'segment_id': self.segment_id,
            'sentence_id': self.sentence_id,
            'chapter_id': self.chapter_id,  # Include chapter_id in serialization
            'segment_index': self.segment_index,
            'segment_text': self.segment_text,
            'english_text': self.english_text,
            'wx_text': self.wx_text,
            'segment_type': self.segment_type,
            'index_type': self.index_type,
            'status': self.status
        }
        if exclude_keys:
            for key in exclude_keys:
                data.pop(key, None)
        return data



from application.extensions import db
import datetime


class Sentence(db.Model):
    __tablename__ = 'sentences'

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    sentence_index = db.Column(db.String, nullable=False)
    sentence_id = db.Column(db.String, nullable=False, unique=True) 
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    chapter = db.relationship('Chapter', backref=db.backref('sentences', lazy=True, order_by="Sentence.sentence_index"))

    # Ensure that the combination of chapter_id and sentence_id is unique
    __table_args__ = (
        db.UniqueConstraint('chapter_id', 'sentence_id', name='_chapter_sentence_uc'),
    )

    @classmethod
    def next_sentence_index(cls, chapter_id):
        last_sentence = cls.query.filter_by(chapter_id=chapter_id).order_by(cls.sentence_index.desc()).first()
        if last_sentence:
            return last_sentence.sentence_index + 1
        return 1



from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from application.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
import traceback

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(JSONB, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    organization = db.Column(db.String(255), nullable=True)
    language = db.Column(JSONB, nullable=False)  # new field for multiple languages
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    projects_uploaded = db.relationship('Project', backref='owner', lazy='dynamic')

    def set_password(self, password):   
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def total_assigned_projects(self):
        if isinstance(self.role, list):
            role_list = self.role
        else:
            role_list = [self.role]
            
        if 'annotator' in role_list or 'reviewer' in role_list:
            return self.projects.count() if hasattr(self, 'projects') else 0
        return 0
    
    def total_uploaded_projects(self):
        if isinstance(self.role, list):
            role_list = self.role
        else:
            role_list = [self.role]
            
        if 'admin' in role_list:
            return self.projects_uploaded.count()
        return 0
    
    def get_reset_token(self, expires_sec=3600):
        try:
            secret_key = current_app.config.get('SECRET_KEY')
            if not secret_key:
                print("ERROR: SECRET_KEY is not set in Flask configuration")
                return None

            s = URLSafeTimedSerializer(secret_key)
            token = s.dumps({'user_id': self.id}, salt='password-reset-salt')
            return token
        except Exception as e:
            print(f"Error generating reset token: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        if not token:
            return None
        try:
            secret_key = current_app.config.get('SECRET_KEY')
            if not secret_key:
                print("ERROR: SECRET_KEY is not set in Flask configuration")
                return None
            s = URLSafeTimedSerializer(secret_key)
            user_data = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
            return User.query.get(user_data['user_id'])
        except Exception as e:
            print(f"Error verifying reset token: {e}")
            traceback.print_exc()
            return None
