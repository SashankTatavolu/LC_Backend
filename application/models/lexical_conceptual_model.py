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
