from application.extensions import db

class Relational(db.Model):
    __tablename__ = 'relational'
    relational_id = db.Column(db.Integer, primary_key=True)
    # segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id', ondelete='CASCADE'), nullable=False)
    segment_index = db.Column(db.String(50), nullable=False)
    index = db.Column(db.Integer)  # Added index column
    # cxn_index = db.Column(db.Integer)  # Commented out as per your schema update
    head_relation = db.Column(db.String(255), nullable=False)
    head_index = db.Column(db.String(255))  # Added main_index column
    dep_relation = db.Column(db.String(255))  # Added relation column
    is_main = db.Column(db.Boolean, default=False)
    concept_id = db.Column(db.Integer, db.ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)  # Added concept_id column
    isFinalized = db.Column(db.Boolean, default=False, nullable=False) 

    segment = db.relationship('Segment', back_populates='relational')
    concept = db.relationship('LexicalConceptual', back_populates='relational')

    def serialize(self):
        return {
            'relational_id': self.relational_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index,  # Added index field in the serialize method
            # 'cxn_index': self.cxn_index,  # Commented out as per your schema update
            'head_relation': self.head_relation,
            'concept_id': self.concept_id , # Added concept_id in the serialize method
            'head_index': self.head_index,
            'dep_relation': self.dep_relation,
            'isFinalized': self.isFinalized
        }
