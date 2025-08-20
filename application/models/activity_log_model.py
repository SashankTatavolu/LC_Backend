from datetime import datetime
from application.extensions import db

class ConceptActivityLog(db.Model):
    __tablename__ = 'concept_activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=True)  # Made nullable since we might not always have it
    ip_address = db.Column(db.String(50), nullable=True)  # Track IP address
    user_agent = db.Column(db.Text, nullable=True)  # Track browser/device info
    action = db.Column(db.String(50), nullable=False)  # 'view', 'edit', 'delete', etc.
    concept_id = db.Column(db.Integer, nullable=True)
    concept_label = db.Column(db.String(255), nullable=True)
    details = db.Column(db.JSON, nullable=True)  # Store additional info
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ConceptActivityLog {self.id} {self.action}>'