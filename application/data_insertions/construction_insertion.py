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

class LexicalConceptual(Base):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    index = Column(Integer, nullable=False)
    concept = Column(String(255), nullable=False)
    relational = relationship('Relational', back_populates='concept')
    constructions = relationship('Construction', back_populates='concept')

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
    isFinalized = Column(Boolean, default=False)
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
    isFinalized = Column(Boolean, default=False)
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

# Create tables
Base.metadata.create_all(bind=engine)



def parse_data_for_construction(file_path):
    constructions = []
    current_segment_id = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    print(f"📂 File {file_path} has {len(lines)} lines.")  # Debugging

    for line in lines:
        line = line.strip()

        # Match both <sent_id=> and <segment_id=>
        match = re.search(r'<(?:sent_id|segment_id)\s*=\s*([\w_\-]+)>', line)
        if match:
            current_segment_id = match.group(1)
            print(f"✅ Parsed segment_id: {current_segment_id}")  # Debugging
            continue

        elif line.startswith("</sent_id>") or line.startswith("</segment_id>"):
            current_segment_id = None
            continue

        elif line.startswith("#") or line.startswith("%") or line.startswith("*"):
            continue  # Skip comments and markers

        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            print(f"🔍 Processing line: {parts}")  # Debugging

            if len(parts) >= 9:  # Ensure there are at least 9 columns
                try:
                    index = int(parts[1])  # Extract the 2nd column as index
                    construction = parts[8]  # Extract the 9th column

                    # Extract cxn_index and component_type from the 9th column
                    if ':' in construction:
                        cxn_index, component_type = construction.split(':', 1)
                    else:
                        cxn_index = "-"
                        component_type = "-"

                    constructions.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'cxn_index': cxn_index.strip(),
                        'component_type': component_type.strip(),
                        'construction': construction
                    })

                except ValueError as e:
                    print(f"⚠️ Error: Invalid format in line: {line} (Segment ID: {current_segment_id}, Error: {e})")
            else:
                print(f"⚠️ Error: Unexpected format in line: {line} {current_segment_id}")

    print(f"🚀 Extracted {len(constructions)} constructions.")  # Debugging
    return constructions


def insert_construction_data(session, file_path, chapter_id):
    try:
        construction_data = parse_data_for_construction(file_path)

        for construction_data_item in construction_data:
            segment_id = construction_data_item['segment_id']
            try:
                # Find the segment using the segment_index and chapter_id
                print(f"Looking for segment_id: {segment_id}, chapter_id: {chapter_id}")
                segment = session.query(Segment).join(Sentence).filter(
                    Segment.segment_index == segment_id,
                    # Sentence.chapter_id == chapter_id
                ).first()
                
                if not segment:
                    print(f"❌ No matching segment found for segment_id {segment_id} in chapter {chapter_id}")
                else:
                    print(f"✅ Found segment: {segment.segment_index}")

                if segment:
                    # Find the lexical_conceptual_id using the segment_id and index
                    lexical_concept = session.query(LexicalConceptual).filter_by(
                        segment_id=segment.segment_id,
                        index=construction_data_item['index']
                    ).first()

                    concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                    # Check if the construction entry already exists before inserting
                    existing_construction_entry = session.query(Construction).filter_by(
                        segment_id=segment.segment_id,
                        segment_index=segment_id
                    ).first()

                    if existing_construction_entry:
                        print(f"Skipping insertion: Construction entry already exists for segment_id {segment_id}, segment_index {segment_id}")
                        continue 

                    # Insert a new construction entry if it does not exist
                    construction = Construction(
                        segment_id=segment.segment_id,
                        segment_index=segment_id,
                        index=construction_data_item['index'],
                        cxn_index=construction_data_item['cxn_index'],
                        component_type=construction_data_item['component_type'],
                        concept_id=concept_id,  # Set the concept_id here
                        construction=construction_data_item['construction']
                    )
                    session.add(construction)
                else:
                    print(f"Error: No matching segment found for segment_index: {segment_id}")

            except Exception as e:
                print(f"Error inserting data for segment_id {segment_id}: {e}")
                session.rollback()

        session.commit()
        print("Construction data inserted successfully!")

    except Exception as e:
        print(f"Error inserting construction data: {e}")
        session.rollback()

    finally:
        session.close()
        print("done")



def main():
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/health_data_part_2/USRS.txt"
    chapter_id = 19
    session = SessionLocal()
    insert_construction_data(session, file_path, chapter_id)

if __name__ == "__main__":
    main()