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
    
