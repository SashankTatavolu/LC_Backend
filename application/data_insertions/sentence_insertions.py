# from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
# from sqlalchemy.orm import declarative_base, sessionmaker
# import datetime

# Base = declarative_base()

# # class Sentence(Base):
# #     __tablename__ = 'sentences'

# #     id = Column(Integer, primary_key=True)
# #     chapter_id = Column(Integer, nullable=False)
# #     sentence_index = Column(Integer, nullable=False)
# #     sentence_id = Column(String, nullable=False)
# #     text = Column(Text, nullable=False)
# #     created_at = Column(DateTime, default=datetime.datetime.utcnow)
# #     updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
# class Sentence(Base):
#     __tablename__ = 'sentences'

#     id = db.Column(db.Integer, primary_key=True)
#     chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
#     sentence_index = db.Column(db.Integer, nullable=False)
#     sentence_id = db.Column(db.String, nullable=False, unique=True) 
#     text = db.Column(db.Text, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

#     chapter = db.relationship('Chapter', backref=db.backref('sentences', lazy=True, order_by="Sentence.sentence_index"))

#     # Ensure that the combination of chapter_id and sentence_id is unique
#     __table_args__ = (
#         db.UniqueConstraint('chapter_id', 'sentence_id', name='_chapter_sentence_uc'),
#     )

#     @classmethod
#     def next_sentence_index(cls, chapter_id):
#         last_sentence = cls.query.filter_by(chapter_id=chapter_id).order_by(cls.sentence_index.desc()).first()
#         if last_sentence:
#             return last_sentence.sentence_index + 1
#         return 1

# def read_sentences_from_file(file_path):
#     import re
#     sentences = []
#     with open(file_path, 'r', encoding='utf-8') as file:
#         for line in file:
#             # Split on any whitespace sequence
#             parts = re.split(r'\s+', line.strip(), maxsplit=1)
#             if len(parts) == 2:
#                 identifier, text = parts
#                 try:
#                     sentence_index = int(re.search(r'\d+$', identifier).group())  # Extract the numeric part at the end and cast to integer
#                     sentences.append({"sentence_index": sentence_index, "sentence_id": identifier, "text": text})
#                 except (ValueError, AttributeError):
#                     print(f"Invalid sentence_index in line: {line}")
#             else:
#                 print(f"Skipping invalid line: {line}")
#     return sentences



# # DATABASE_URL = 'postgresql://postgres:Sashank123@localhost/testdb'
# DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc'

# engine = create_engine(DATABASE_URL)

# Session = sessionmaker(bind=engine)

# session = Session()

# Base.metadata.create_all(engine)

# sentence_file_path = 'application/data_insertions/test_insert/Test_1_input_to_Segmenter'
# # sentence_file_path = 'application/data_insertions/10th chapter/10nios_original.txt'

# sentences_data = read_sentences_from_file(sentence_file_path)

# # for sentence_data in sentences_data:
# #     sentence_data["chapter_id"] = 36  # Adjust this value as needed
# #     new_sentence = Sentence(**sentence_data)
# #     session.add(new_sentence)

# for sentence_data in sentences_data:
#     sentence_data["chapter_id"] = 9 # Adjust this value as needed
#     new_sentence = Sentence(**sentence_data)
#     session.add(new_sentence)

# session.commit()

# print("Sentence data inserted successfully.")

# # from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
# # from sqlalchemy.orm import declarative_base, sessionmaker
# # import datetime

# # Base = declarative_base()

# # class Sentence(Base):
# #     __tablename__ = 'sentences'

# #     id = Column(Integer, primary_key=True)
# #     chapter_id = Column(Integer, nullable=False)
# #     sentence_index = Column(Integer, nullable=False)
# #     sentence_id = Column(String, nullable=False, unique=True)
# #     text = Column(Text, nullable=False)
# #     created_at = Column(DateTime, default=datetime.datetime.utcnow)
# #     updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# # def read_sentences_from_file(file_path):
# #     import re
# #     sentences = []
# #     current_chapter_id = None
# #     current_sentence_index = 1

# #     with open(file_path, 'r', encoding='utf-8') as file:
# #         for line in file:
# #             parts = re.split(r'\s+', line.strip(), maxsplit=1)
# #             if len(parts) == 2:
# #                 identifier, text = parts
# #                 chapter_id = 36  # Adjust this value as needed
# #                 if current_chapter_id is None:
# #                     current_chapter_id = chapter_id
# #                 if current_chapter_id != chapter_id:
# #                     current_chapter_id = chapter_id
# #                     current_sentence_index = 1

# #                 sentences.append({
# #                     "chapter_id": current_chapter_id,
# #                     "sentence_index": current_sentence_index,
# #                     "sentence_id": identifier,
# #                     "text": text
# #                 })
# #                 current_sentence_index += 1
# #             else:
# #                 print(f"Skipping invalid line: {line}")
# #     return sentences

# # DATABASE_URL = 'postgresql://postgres:Sashank123@localhost/testdb'

# # engine = create_engine(DATABASE_URL)
# # Session = sessionmaker(bind=engine)
# # session = Session()

# # Base.metadata.create_all(engine)

# # sentence_file_path = 'application/data_insertions/data1/1ch_nios_original.txt'

# # sentences_data = read_sentences_from_file(sentence_file_path)

# # for sentence_data in sentences_data:
# #     new_sentence = Sentence(**sentence_data)
# #     session.add(new_sentence)

# # session.commit()

# # print("Sentence data inserted successfully.")

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
                    sentence_index = int(re.search(r'\d+$', identifier).group())  # Extract number from identifier
                    sentences.append({"sentence_index": sentence_index, "sentence_id": identifier, "text": text})
                except (ValueError, AttributeError):
                    print(f"Invalid sentence_index in line: {line}")
            else:
                print(f"Skipping invalid line: {line}")
    return sentences

DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"

# DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Ensure all tables are created (only needed if you're creating new tables)
Base.metadata.create_all(engine)

# Path to sentence file
sentence_file_path = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo_data/sentences.txt'

# Read the sentence data from the file
sentences_data = read_sentences_from_file(sentence_file_path)

# Insert sentences into the database
for sentence_data in sentences_data:
    sentence_data["chapter_id"] = 1 # Specify the chapter ID for these sentences
    new_sentence = Sentence(**sentence_data)
    session.add(new_sentence)

# Commit the transaction to persist the data in the database
session.commit()

print("Sentence data inserted successfully.")
