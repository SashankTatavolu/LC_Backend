from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

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

def read_chapter_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# DATABASE_URL = 'postgresql://postgres:Sashank123@localhost/testdb'
DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'


engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)

session = Session()

Base.metadata.create_all(engine)


chapter_file_path = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/input.txt'

chapter_text = read_chapter_from_file(chapter_file_path)


chapter_data = {
    "project_id":13,
    "name": "Geonios_15ch",  
    "uploaded_by_id": 24, 
    "text": chapter_text,
    "created_at": datetime.datetime.utcnow(),
    "updated_at": datetime.datetime.utcnow(),
}

new_chapter = Chapter(**chapter_data)
session.add(new_chapter)

session.commit()

print("Chapter data inserted successfully.")
