from application.extensions import db

class Segment(db.Model):
    __tablename__ = 'segments'

    segment_id = db.Column(db.Integer, primary_key=True)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentences.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)  # Add chapter_id
    segment_index = db.Column(db.String(50))
    segment_text = db.Column(db.Text, nullable=False)
    english_text = db.Column(db.Text, nullable=False)  # English text column
    wx_text = db.Column(db.Text, nullable=False)
    segment_type = db.Column(db.String(50))
    index_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')

    # Relationships
    sentence = db.relationship('Sentence', backref=db.backref('segments', lazy=True))
    chapter = db.relationship('Chapter', backref=db.backref('segments', lazy=True))  # Add relationship to Chapter

    lexical_concepts = db.relationship('LexicalConceptual', back_populates='segment')
    relational = db.relationship('Relational', back_populates='segment')
    discourse = db.relationship('Discourse', back_populates='segment')
    construction = db.relationship('Construction', back_populates='segment')
    generations = db.relationship("Generation", back_populates="segment")

    # Serialization
    def serialize(self):
        return {
            'segment_id': self.segment_id,
            'sentence_id': self.sentence_id,
            'chapter_id': self.chapter_id,  # Include chapter_id in serialization
            'segment_index': self.segment_index,
            'segment_text': self.segment_text,
            'english_text': self.english_text,
            'wx_text': self.wx_text,
            'segment_type': self.segment_type,
            'index_type': self.index_type,
            'status': self.status
        }

    def serialize(self, exclude_keys=None):
        data = {
            'segment_id': self.segment_id,
            'sentence_id': self.sentence_id,
            'chapter_id': self.chapter_id,  # Include chapter_id in serialization
            'segment_index': self.segment_index,
            'segment_text': self.segment_text,
            'english_text': self.english_text,
            'wx_text': self.wx_text,
            'segment_type': self.segment_type,
            'index_type': self.index_type,
            'status': self.status
        }
        if exclude_keys:
            for key in exclude_keys:
                data.pop(key, None)
        return data
