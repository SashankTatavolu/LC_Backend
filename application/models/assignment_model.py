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
