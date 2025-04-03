import re
from sqlalchemy import Boolean, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

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
    lexical_concepts = relationship("LexicalConceptual", back_populates="segment")

class LexicalConceptual(Base):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False) 
    index = Column(Integer)
    concept = Column(String(255), nullable=False)
    semantic_category = Column(String(255))
    isFinalized = Column(Boolean, default=False) 
    morpho_semantics = Column(String(255))
    speakers_view = Column(String(255))
    segment = relationship('Segment', back_populates='lexical_concepts')

Base.metadata.create_all(bind=engine)
# def parse_data(file_path):
#     lexical_concepts = []
#     current_segment_id = None

#     with open(file_path, 'r', encoding='utf-8') as file:
#         lines = file.readlines()

#     print(f"File {file_path} has {len(lines)} lines.")  # Debugging
#     for i, line in enumerate(lines[:10]):  # Print first 10 lines
#         print(f"Line {i+1}: {line.strip()}")

#     for line in lines:
#         line = line.strip()
#         if line.startswith("<sent_id="):
#             match = re.search(r'<sent_id\s*=\s*([\w_\-]+)>', line)
#             if match:
#                 current_segment_id = match.group(1)
#                 print(f"Parsed segment_id: {current_segment_id}")  # Debugging
#             else:
#                 print(f"Error: Unable to parse sent_id in line: {line}")
#                 current_segment_id = None
#         elif line.startswith("</sent_id>"):
#             current_segment_id = None
#         elif line.startswith("#") or line.startswith("%"):
#             continue  # Skip comments and markers
#         elif line and current_segment_id is not None:
#             parts = re.split(r'\s+', line)
#             print(f"Processing line: {parts}")  # Debugging

#             # Ensure parts has at least required indices
#             concept = parts[0] if len(parts) > 0 else None
#             index = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
#             semantic_category = parts[2] if len(parts) > 2 else None
#             morpho_semantics = parts[3] if len(parts) > 3 else None
#             speakers_view = parts[6] if len(parts) > 6 else None

#             if concept and index is not None:
#                 lexical_concepts.append({
#                     'segment_id': current_segment_id,
#                     'index': index,
#                     'concept': concept,
#                     'semantic_category': semantic_category,
#                     'morpho_semantics': morpho_semantics,
#                     'speakers_view': speakers_view
#                 })
#             else:
#                 print(f"Skipping malformed line: {line}")

#     print(f"Extracted {len(lexical_concepts)} lexical concepts.")  # Debugging
#     return lexical_concepts




def parse_data(file_path):
    lexical_concepts = []
    current_segment_id = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    print(f"File {file_path} has {len(lines)} lines.")  # Debugging

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
        
        elif line.startswith("#") or line.startswith("%"):
            continue  # Skip comments and markers

        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            print(f"🔍 Processing line: {parts}")  # Debugging

            # Ensure parts has at least required indices
            concept = parts[0] if len(parts) > 0 else None
            index = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            semantic_category = parts[2] if len(parts) > 2 else None
            morpho_semantics = parts[3] if len(parts) > 3 else None
            speakers_view = parts[6] if len(parts) > 6 else None

            if concept and index is not None:
                lexical_concepts.append({
                    'segment_id': current_segment_id,
                    'index': index,
                    'concept': concept,
                    'semantic_category': semantic_category,
                    'morpho_semantics': morpho_semantics,
                    'speakers_view': speakers_view
                })
            else:
                print(f"⚠️ Skipping malformed line: {line}")

    print(f"🚀 Extracted {len(lexical_concepts)} lexical concepts.")  # Debugging
    return lexical_concepts

def insert_data(session, file_path, chapter_id):
    try:
        data = parse_data(file_path)
        print(f"Parsed {len(data)} lexical concepts from file.")  # Debugging

        for segment_data in data:
            # Find the segment
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_data['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()

            print(f"Checking segment: {segment_data['segment_id']}")  # Debugging
            if segment:
                print(f"Found segment: {segment.segment_id}")

                # Check if the lexical concept already exists
                existing_lexical_concept = session.query(LexicalConceptual).join(Segment).join(Sentence).filter(
                    LexicalConceptual.segment_id == segment.segment_id,
                    LexicalConceptual.segment_index == segment_data['segment_id'],
                    Sentence.chapter_id == chapter_id
                ).first()

                if existing_lexical_concept:
                    print(f"Skipping insertion: Lexical concept already exists for segment_index {segment_data['segment_id']}, index {segment_data['index']}")
                    continue

                # Create and add new lexical concept
                lexical_concept = LexicalConceptual(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index'],
                    concept=segment_data['concept'],
                    semantic_category=segment_data['semantic_category'],
                    morpho_semantics=segment_data['morpho_semantics'],
                    speakers_view=segment_data['speakers_view']
                )
                print(f"Inserting: {lexical_concept}")  # Debugging
                session.add(lexical_concept)
            else:
                print(f"Error: No matching segment found for segment_index: {segment_data['segment_id']} in chapter {chapter_id}")

        session.commit()
        print("Data inserted successfully!")

    except Exception as e:
        print(f"Error inserting data: {e}")
        session.rollback()

    finally:
        session.close()
        print("done")


def main():
    # file_path = "application/data_insertions/10th chapter/test.txt"
    file_path = "/home/sashank/Downloads/LC_Backend-main/application/data_insertions/health_data/health_data_part_2/USRS.txt"
    
    chapter_id = 20# Specify the chapter_id you're working with

    session = SessionLocal()
    insert_data(session, file_path, chapter_id)

if __name__ == "__main__":
    main()
