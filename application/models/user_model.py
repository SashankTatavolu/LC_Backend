
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
