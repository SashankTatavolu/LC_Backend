import re
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import datetime

# Database configuration
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"

SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'
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
    __tablename__ = "sentences"
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    sentence_index = Column(String, index=True)
    sentence_id = Column(String, nullable=False, unique=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    segments = relationship("Segment", back_populates="sentence")

# Segment model
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
    construction = relationship("Construction", back_populates="segment")
    discourse = relationship("Discourse", back_populates="segment")

class LexicalConceptual(Base):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    index = Column(Integer, nullable=False)
    concept = Column(String(255), nullable=False)
    relational = relationship('Relational', back_populates='concept')
    constructions = relationship('Construction', back_populates='concept')
    discourse = relationship('Discourse', back_populates='concept')

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

# Construction model
class Construction(Base):
    __tablename__ = 'construction'
    construction_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    index = Column(Integer)  # Added index column
    cxn_index = Column(String(50))  # Added cxn_index column
    component_type = Column(String(255))  # Added component_type column
    concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)  # Added concept_id column
    construction = Column(String(50), nullable=False)
    segment = relationship('Segment', back_populates='construction')
    concept = relationship('LexicalConceptual', back_populates='constructions')

    def serialize(self):
        return {
            'construction_id': self.construction_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index,  # Include index in serialization
            'cxn_index': self.cxn_index,  # Include cxn_index in serialization
            'component_type': self.component_type,  # Include component_type in serialization
            'concept_id': self.concept_id,  # Include concept_id in serialization
            'construction': self.construction
        }

# Discourse model
class Discourse(Base):
    __tablename__ = 'discourse'
    discourse_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    discourse = Column(String(50))
    index = Column(Integer) 
    head_index = Column(String(50))  
    relation = Column(String(255)) 
    segment = relationship('Segment', back_populates='discourse')
    concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True) 
    concept = relationship('LexicalConceptual', back_populates='discourse')

    def serialize(self):
        return {
            'discourse_id': self.discourse_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index, 
            'head_index': self.head_index,
            'relation': self.relation,
            'concept_id': self.concept_id, 
            'discourse': self.discourse
        }

# Create tables
Base.metadata.create_all(bind=engine)

def parse_data_for_discourse(file_path):
    discourses = []
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
            if len(parts) >= 5:  # Ensure there are at least 5 columns
                try:
                    index = int(parts[1])
                    discourse = parts[5]  # Extract the 5th column

                    if ':' in discourse:
                        head_index, relation = discourse.split(':', 1)
                    else:
                        head_index = "-"
                        relation = "-"

                    discourses.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'head_index': head_index.strip(),
                        'relation': relation.strip(),
                        'discourse': discourse
                    })
                except ValueError:
                    print(f"Error: Invalid format in line: {line}")
            else:
                print(f"Error: Unexpected format in line: {line}")

    return discourses

# def insert_discourse_data(session, file_path, chapter_id):
#     try:
#         discourse_data = parse_data_for_discourse(file_path)

#         for discourse_data_item in discourse_data:
#             segment_id = discourse_data_item['segment_id']
#             # segment = session.query(Segment).filter_by(segment_index=discourse_data_item['segment_id']).first()
#             segment = session.query(Segment).join(Sentence).filter(
#                     Segment.segment_index == segment_id,
#                     Sentence.chapter_id == chapter_id
#                 ).first()

#             if segment:

#                 # Find the lexical_conceptual_id using the segment_id and index
#                 lexical_concept = session.query(LexicalConceptual).filter_by(
#                     segment_id=segment.segment_id,
#                     index=discourse_data_item['index']
#                 ).first()

#                 concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

#                 discourse = Discourse(
#                     segment_id=segment.segment_id,
#                     segment_index=discourse_data_item['segment_id'],
#                     index=discourse_data_item['index'],
#                     head_index=discourse_data_item['head_index'],
#                     relation=discourse_data_item['relation'],
#                     concept_id=concept_id,
#                     discourse=discourse_data_item['discourse']
#                 )
#                 session.add(discourse)
#             else:
#                 print(f"Error: No matching segment found for segment_index: {discourse_data_item['segment_id']}")

#         session.commit()
#         print("Discourse data inserted successfully!")

#     except Exception as e:
#         print(f"Error inserting discourse data: {e}")
#         session.rollback()

#     finally:
#         session.close()

def insert_discourse_data(session, file_path, chapter_id):
    try:
        discourse_data = parse_data_for_discourse(file_path)

        for discourse_data_item in discourse_data:
            segment_id = discourse_data_item['segment_id']

            # Query the Segment based on segment_index and chapter_id
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_id,
                Sentence.chapter_id == chapter_id
            ).first()

            if segment:
                # Check if a discourse entry already exists based on segment_id and segment_index
                existing_discourse_entry = session.query(Discourse).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=segment_id
                ).first()

                if existing_discourse_entry:
                    print(f"Skipping insertion: Discourse entry already exists for segment_id {segment_id}, segment_index {segment_id}")
                    continue  # Skip this entry if it already exists

                # Find the lexical_conceptual_id using the segment_id and index
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=discourse_data_item['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                # Insert new Discourse entry
                discourse = Discourse(
                    segment_id=segment.segment_id,
                    segment_index=discourse_data_item['segment_id'],
                    index=discourse_data_item['index'],
                    head_index=discourse_data_item['head_index'],
                    relation=discourse_data_item['relation'],
                    concept_id=concept_id,
                    discourse=discourse_data_item['discourse']
                )
                session.add(discourse)
            else:
                print(f"Error: No matching segment found for segment_index: {discourse_data_item['segment_id']}")

        session.commit()
        print("Discourse data inserted successfully!")

    except Exception as e:
        print(f"Error inserting discourse data: {e}")
        session.rollback()

    finally:
        session.close()
        print("done")


def main():
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/Ecommerce_data/USRs.txt"
    chapter_id = 18
    session = SessionLocal()
    insert_discourse_data(session, file_path, chapter_id)

if __name__ == "__main__":
    main()
