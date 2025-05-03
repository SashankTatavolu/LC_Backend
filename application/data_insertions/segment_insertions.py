import datetime
import re
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# SQLAlchemy database setup

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password123@10.2.8.12/lc4u"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Sentence(Base):
    __tablename__ = "sentences"
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    sentence_index = Column(String, index=True)
    sentence_id = Column(String, nullable=False)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    segments = relationship("Segment", back_populates="sentence")

class Chapter(Base):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    uploaded_by_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Segment(Base):
    __tablename__ = "segments"
    segment_id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(Integer, ForeignKey('sentences.id'))
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=False)
    segment_index = Column(String)
    segment_text = Column(Text)
    english_text = Column(Text, nullable=True)  # Allow NULL values
    wx_text = Column(Text, nullable=True)  # Allow NULL values
    segment_type = Column(String)
    index_type = Column(String)
    sentence = relationship("Sentence", back_populates="segments")
    chapter = relationship('Chapter', backref='segments')

Base.metadata.create_all(bind=engine)

def main():
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/Segments.txt"
    chapter_id = 44 # Example: Use the specific chapter_id for the sentences

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    session = SessionLocal()

    try:
        for line in lines:
            line = line.strip()
            # Match the segment index at the beginning (e.g., Geo_nios_13ch_0020a)
            match = re.match(r'^([^\s]+)\s+(.*)', line)
            if not match:
                print(f"Skipping invalid line: {line}")
                continue

            segment_index = match.group(1)
            rest_of_line = match.group(2)

            # Now split the remaining parts: segment_text, wx_text, english_text
            parts = re.split(r'\s{2,}|\t+', rest_of_line)
            if len(parts) < 1:
                print(f"Skipping incomplete line: {line}")
                continue

            segment_text = parts[0]
            wx_text = parts[1] if len(parts) > 1 else None
            english_text = parts[2] if len(parts) > 2 else None

            # Extract the sentence_id (without trailing character)
            extracted_sentence_id = segment_index.rstrip('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

            sentence = session.query(Sentence).filter(
                Sentence.sentence_id == extracted_sentence_id,
                Sentence.chapter_id == chapter_id
            ).first()
            # sentence = session.query(Sentence).filter(
            #     and_(
            #         Sentence.sentence_id.like(f"{extracted_sentence_id}%"),
            #         Sentence.chapter_id == chapter_id
            #     )
            # ).first()
            
            if sentence:
                sentence_id = sentence.id

                new_segment = Segment(
                    sentence_id=sentence_id,
                    segment_index=segment_index,
                    chapter_id=chapter_id,
                    segment_text=segment_text,
                    english_text=english_text,
                    wx_text=wx_text,
                    segment_type=" ",
                    index_type="type"
                )
                session.add(new_segment)
            else:
                print(f"Sentence with id {extracted_sentence_id} not found.")

        session.commit()
        print("Segments inserted successfully!")

    except Exception as e:
        print(f"Error inserting segments: {e}")
        session.rollback()

    finally:
        session.close()
        print("done")

if __name__ == "__main__":
    main()



