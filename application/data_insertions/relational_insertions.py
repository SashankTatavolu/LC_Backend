import re
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import datetime

# Database configuration
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database models
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
    __tablename__ = "sentences"
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    sentence_index = Column(String, index=True)
    sentence_id = Column(String, nullable=False, unique=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    segments = relationship("Segment", back_populates="sentence")

class Segment(Base):
    __tablename__ = 'segments'
    segment_id = Column(Integer, primary_key=True)
    sentence_id = Column(Integer, ForeignKey('sentences.id'), nullable=False)
    segment_index = Column(String(50))
    segment_text = Column(Text, nullable=False)
    english_text = Column(Text, nullable=False)
    wx_text = Column(Text, nullable=False)
    segment_type = Column(String(50))
    index_type = Column(String(20), nullable=False)
    sentence = relationship("Sentence", back_populates="segments")
    relational = relationship('Relational', back_populates='segment')

class LexicalConceptual(Base):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    index = Column(Integer, nullable=False)
    concept = Column(String(255), nullable=False)
    relational = relationship('Relational', back_populates='concept')

class Relational(Base):
    __tablename__ = 'relational'
    relational_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    index = Column(Integer)  # Added index column
    # cxn_index = Column(Integer)  # Changed column name here
    head_relation = Column(String(255), nullable=False)
    head_index = Column(String(255))  # Added main_index column
    dep_relation = Column(String(255))  # Added relation column
    is_main = Column(Boolean, default=False)
    concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)  # Added concept_id column
    segment = relationship('Segment', back_populates='relational')
    concept = relationship('LexicalConceptual', back_populates='relational')

Base.metadata.create_all(bind=engine)

def parse_data(file_path):
    relational_data = []
    current_segment_id = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("<sent_id="):
            match = re.search(r'<sent_id\s*=\s*([\w_\-]+)>', line)
            if match:
                current_segment_id = match.group(1)
            else:
                current_segment_id = None
        elif line.startswith("</sent_id>"):
            current_segment_id = None
        elif line.startswith("#") or line.startswith("%") or line.startswith("*"):
            continue  # Skip comments and affirmative marker
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            if len(parts) >= 2:
                try:
                    index = int(parts[1])
                    head_relation = parts[4] 
                    if ':' in parts[4]:
                        head_index, dep_relation = parts[4].split(':', 1)
                        head_index = head_index.strip() if head_index.strip().isdigit() else "-"
                        dep_relation = dep_relation.strip()
                    else:
                        head_index = "-"
                        dep_relation = "-"

                    is_main = head_relation.strip() == "0:main"  # Determine if the component_type indicates a main entry
                    print(head_index,dep_relation)
                    relational_data.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'head_relation': head_relation,
                        'head_index': head_index,
                        'dep_relation': dep_relation,
                        'is_main': is_main
                    })
                except ValueError:
                    pass

    return relational_data

# def insert_relational_data(session, file_path, chapter_id):
#     try:
#         data = parse_data(file_path)

#         for segment_data in data:
#             # Find the segment using the segment_index (parsed segment_id)
#             # segment = session.query(Segment).filter_by(segment_index=segment_data['segment_id']).first()
#             # Join Segment with Sentence to find the segment using the segment_index and chapter_id
#             segment = session.query(Segment).join(Sentence).filter(
#                 Segment.segment_index == segment_data['segment_id'],
#                 Sentence.chapter_id == chapter_id
#             ).first()
            
#             if segment:
#                 # Find the lexical_conceptual_id using the segment_id and index
#                 lexical_concept = session.query(LexicalConceptual).filter_by(
#                     segment_id=segment.segment_id,
#                     index=segment_data['index']
#                 ).first()

#                 concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

#                 relational_entry = Relational(
#                     segment_id=segment.segment_id,
#                     segment_index=segment_data['segment_id'],
#                     index=segment_data['index'],
#                     main_index=segment_data['main_index'],
#                     relation=segment_data['relation'],
#                     component_type=segment_data['component_type'],
#                     is_main=segment_data['is_main'],
#                     concept_id=concept_id  # Set the concept_id here
#                 )
#                 session.add(relational_entry)
#             else:
#                 print(f"Error: No matching segment found for segment_index: {segment_data['segment_id']}")

#         session.commit()
#         print("Data inserted successfully!")

#     except Exception as e:
#         print(f"Error inserting data: {e}")
#         session.rollback()

#     finally:
#         session.close()

def insert_relational_data(session, file_path, chapter_id):
    try:
        data = parse_data(file_path)

        for segment_data in data:
            # Find the segment using the segment_index and chapter_id
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_data['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()
            
            if segment:
                # Find the lexical_conceptual_id using the segment_id and index
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=segment_data['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                # Check if the relational entry already exists before inserting
                existing_relational_entry = session.query(Relational).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id']
                ).first()

                if existing_relational_entry:
                    print(f"Skipping insertion: Relational entry already exists for segment_id {segment_data['segment_id']}, segment_index {segment_data['index']}")
                    continue

                # Insert a new relational entry if it does not exist
                relational_entry = Relational(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index'],
                    head_index=segment_data['head_index'],
                    dep_relation=segment_data['dep_relation'],
                    head_relation=segment_data['head_relation'],
                    is_main=segment_data['is_main'],
                    concept_id=concept_id  # Set the concept_id here
                )
                session.add(relational_entry)
            else:
                print(f"Error: No matching segment found for segment_index: {segment_data['segment_id']}")

        session.commit()
        print("Data inserted successfully!")

    except Exception as e:
        print(f"Error inserting data: {e}")
        session.rollback()

    finally:
        session.close()


def main():
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo_data/USRS.txt"
    chapter_id = 1  # Example chapter_id, update it as needed
    session = SessionLocal()
    insert_relational_data(session, file_path, chapter_id)

if __name__ == "__main__":
    main()

