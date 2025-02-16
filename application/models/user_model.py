from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from application.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(JSONB, nullable=False)
    organization = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    projects_uploaded = db.relationship('Project', backref='owner', lazy='dynamic')

    def set_password(self, password):   
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def total_assigned_projects(self):
        if self.role in ['annotator', 'reviewer']:
            return self.projects.count()
        return 0
    
    def total_uploaded_projects(self):
        if self.role == 'admin':
            return self.projects_uploaded.count()
        return 0
