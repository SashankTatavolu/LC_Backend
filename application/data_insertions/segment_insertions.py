import datetime
import re
from sqlalchemy import create_engine
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
    file_path = "/home/sashank/Downloads/LC_Backend-main/application/data_insertions/health_data/health_data_part_2/segments.txt"
    chapter_id = 20 # Example: Use the specific chapter_id for the sentences

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    session = SessionLocal()

    try:
        for line in lines:
            # Adjust the split regex to handle spaces or tabs
            parts = re.split(r'\s{2,}|\t+', line.strip())  
            print(f"Line parts: {parts}")  

            # Ensure there are at least 2 parts (segment index & text)
            if len(parts) < 2:
                print(f"Skipping invalid line: {line}")
                continue

            segment_index = parts[0]  # First occurrence of the segment index
            segment_text = parts[1]  # Sentence in the original language
            wx_text = parts[2] if len(parts) > 2 else None  # Handle missing WX text
            english_text = parts[3] if len(parts) > 3 else None  # Handle missing English text

            # extracted_sentence_id = segment_index.rstrip('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
            extracted_sentence_id = segment_index  # Keep full ID

            # Fetch the sentence using both sentence_id and chapter_id
            sentence = session.query(Sentence).filter(
                Sentence.sentence_id == extracted_sentence_id,
                Sentence.chapter_id == chapter_id
            ).first()
            
            if sentence:
                sentence_id = sentence.id

                new_segment = Segment(
                    sentence_id=sentence_id,
                    segment_index=segment_index,
                    chapter_id=chapter_id,
                    segment_text=segment_text,
                    english_text=english_text,  # Allowing None
                    wx_text=wx_text,  # Allowing None
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


