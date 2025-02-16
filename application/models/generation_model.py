from application.extensions import db
from datetime import datetime

class Generation(db.Model):
    __tablename__ = 'generations'

    generation_id = db.Column(db.Integer, primary_key=True)  
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.segment_id'), nullable=False)  
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)  
    generated_text = db.Column(db.Text, nullable=False)  
    segment_index = db.Column(db.String, nullable=False)
    segment = db.relationship('Segment', back_populates='generations')  
    chapter = db.relationship('Chapter', back_populates='generations') 

    def serialize(self):
        return {
            'generation_id': self.generation_id,
            'segment_id': self.segment_id,
            'chapter_id': self.chapter_id,
            'segment_index': self.segment_index,
            'generated_text': self.generated_text
        }

# CREATE TABLE generations (
#     generation_id SERIAL PRIMARY KEY,  -- Primary key with auto-increment
#     segment_id INT NOT NULL,  -- Foreign key to the segments table
#     chapter_id INT NOT NULL,  -- Foreign key to the chapters table
#     generated_text TEXT NOT NULL,  -- The generated text
    
#     -- Foreign key constraints
#     CONSTRAINT fk_segment FOREIGN KEY(segment_id) REFERENCES segments(segment_id) ON DELETE CASCADE,
#     CONSTRAINT fk_chapter FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
# );

# ALTER TABLE generations
# ADD COLUMN segment_index VARCHAR NOT NULL;

