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

