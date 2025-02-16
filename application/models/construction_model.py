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


