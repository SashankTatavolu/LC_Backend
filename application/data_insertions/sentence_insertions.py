from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import re

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

# Define Sentence model with composite unique constraint
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

    # Composite unique constraint for chapter_id and sentence_id
    __table_args__ = (
        UniqueConstraint('chapter_id', 'sentence_id', name='_chapter_sentence_uc'),
    )

    @classmethod
    def next_sentence_index(cls, session, chapter_id):
        last_sentence = session.query(cls).filter_by(chapter_id=chapter_id).order_by(cls.sentence_index.desc()).first()
        if last_sentence:
            return last_sentence.sentence_index + 1
        return 1


# Function to read sentences from a file and parse them
def read_sentences_from_file(file_path):
    sentences = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = re.split(r'\s+', line.strip(), maxsplit=1)
            if len(parts) == 2:
                identifier, text = parts
                try:
                    match = re.search(r'(\d+)(?:[A-Za-z_]*)$', identifier)
                    if match:
                        sentence_index = int(match.group(1))
                    else:
                        print(f"Invalid sentence_index in line: {line}")
                        continue

                    sentences.append({"sentence_index": sentence_index, "sentence_id": identifier, "text": text})
                except (ValueError, AttributeError):
                    print(f"Invalid sentence_index in line: {line}")
            else:
                print(f"Skipping invalid line: {line}")
    return sentences

# DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"

DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Ensure all tables are created (only needed if you're creating new tables)
Base.metadata.create_all(engine)

# Path to sentence file
sentence_file_path = '/home/sashank/Downloads/LC_Backend-main/application/data_insertions/health_data/health_data_part_2/sentences.txt'

# Read the sentence data from the file
sentences_data = read_sentences_from_file(sentence_file_path)

# Insert sentences into the database
for sentence_data in sentences_data:
    sentence_data["chapter_id"] = 20 # Specify the chapter ID for these sentences
    new_sentence = Sentence(**sentence_data)
    session.add(new_sentence)

# Commit the transaction to persist the data in the database
session.commit()

print("Sentence data inserted successfully.")
