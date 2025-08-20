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
