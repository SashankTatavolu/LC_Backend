import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc_platform'
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Chapter(Base):
    __tablename__ = 'chapters'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    uploaded_by_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Sentence(Base):
    __tablename__ = 'sentences'

    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=False)
    sentence_index = Column(Integer, nullable=False)
    sentence_id = Column(String, nullable=False) 
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    chapter = relationship('Chapter', backref='sentences')

    __table_args__ = (
        UniqueConstraint('chapter_id', 'sentence_id', name='_chapter_sentence_uc'),
    )

class Segment(Base):
    __tablename__ = "segments"
    segment_id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(Integer, ForeignKey('sentences.id'))
    segment_index = Column(String)
    segment_text = Column(Text)
    english_text = Column(Text, nullable=False)
    wx_text = Column(Text, nullable=False)
    segment_type = Column(String(255))
    index_type = Column(String)

Base.metadata.create_all(bind=engine)

def main():
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo_data/USRS.txt"  # Update this to your file path
    chapter_id = 1 # Set the chapter ID for filtering segments

    session = SessionLocal()

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        current_sentence_id = None
        segment_type = None

        for line in lines:
            line = line.strip()
            if line.startswith("<sent_id="):
                current_sentence_id = line.split('=')[1].strip('>').strip()
                segment_type = None  

            elif line.startswith("%"):
                segment_type = line.strip()  # Keep the '%' character

            elif current_sentence_id and segment_type:
                print(current_sentence_id)
                print(segment_type)
                parts = line.strip().split('\t')
                if len(parts) > 0:
                    segment_index = current_sentence_id  # Use the first part as segment index

                    segments = session.query(Segment).filter(
                        Segment.segment_index == segment_index,
                        Segment.sentence_id.in_(
                            session.query(Sentence.id).filter(Sentence.chapter_id == chapter_id)
                        )
                    ).all()

                    if segments:
                        for segment in segments:
                            segment.segment_type = segment_type  
                            session.add(segment)  
                    else:
                        print(f"No segments found with index {segment_index} in chapter {chapter_id}.")

        session.commit()  

    except Exception as e:
        print(f"Error updating segment types: {e}")
        session.rollback()

    finally:
        print("done")
        session.close()

if __name__ == "__main__":
    main()
