from application.extensions import db
import datetime


class Sentence(db.Model):
    __tablename__ = 'sentences'

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    sentence_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    chapter = db.relationship('Chapter', backref=db.backref('sentences', lazy=True, order_by="Sentence.sentence_index"))

    @classmethod
    def next_sentence_index(cls, chapter_id):
        last_sentence = cls.query.filter_by(chapter_id=chapter_id).order_by(cls.sentence_index.desc()).first()
        if last_sentence:
            return last_sentence.sentence_index + 1
        return 1
