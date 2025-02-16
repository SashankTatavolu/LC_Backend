# from application.extensions import db

# class DomainTerm(db.Model):
#     __tablename__ = 'domain_terms'
    
#     domain_term_id = db.Column(db.Integer, primary_key=True)
#     segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id', ondelete='CASCADE'), nullable=False)
#     segment_index = db.Column(db.String(50), nullable=False)
#     domain_term = db.Column(db.String(255))
#     index = db.Column(db.Integer, nullable=False)  
#     concept_id = db.Column(db.Integer, db.ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)

#     segment = db.relationship('Segment', back_populates='domain_terms')
#     concept = db.relationship('LexicalConceptual', back_populates='domain_terms')

#     def serialize(self):
#         return {
#             'domain_term_id': self.domain_term_id,
#             'segment_id': self.segment_id,
#             'segment_index': self.segment_index,
#             'domain_term': self.domain_term,
#             'index': self.index,
#             'concept_id': self.concept_id
#         }
