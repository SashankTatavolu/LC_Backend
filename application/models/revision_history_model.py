from sqlalchemy import JSON
from application.extensions import db
from datetime import datetime

class RevisionHistory(db.Model):
    __tablename__ = 'revision_history'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=True)
    chapter_id = db.Column(db.Integer, nullable=True)
    segment_id = db.Column(db.Integer, nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Store user ID
    username = db.Column(db.String(80), nullable=False)  # Store username as well

    change_type = db.Column(db.String(50), nullable=False)
    old_data = db.Column(JSON, nullable=True)
    new_data = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
