import re
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import datetime

# Database configuration
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"


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
    lexical_concepts = relationship("LexicalConceptual", back_populates="segment")
    relational = relationship("Relational", back_populates="segment")
    construction = relationship("Construction", back_populates="segment")
    discourse = relationship("Discourse", back_populates="segment")

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
    relational = relationship('Relational', back_populates='concept')
    constructions = relationship('Construction', back_populates='concept')
    discourse = relationship('Discourse', back_populates='concept')

class Relational(Base):
    __tablename__ = 'relational'
    relational_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    index = Column(Integer)
    head_relation = Column(String(255), nullable=False)
    head_index = Column(String(255))
    dep_relation = Column(String(255))
    is_main = Column(Boolean, default=False)
    concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)
    segment = relationship('Segment', back_populates='relational')
    concept = relationship('LexicalConceptual', back_populates='relational')
    isFinalized = Column(Boolean, default=False) 

class Construction(Base):
    __tablename__ = 'construction'
    construction_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    index = Column(Integer)
    cxn_index = Column(String(50))
    isFinalized = Column(Boolean, default=False)
    component_type = Column(String(255))
    concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)
    construction = Column(String(50), nullable=False)
    segment = relationship('Segment', back_populates='construction')
    concept = relationship('LexicalConceptual', back_populates='constructions')

    def serialize(self):
        return {
            'construction_id': self.construction_id,
            'segment_id': self.segment_id,
            'segment_index': self.segment_index,
            'index': self.index,
            'cxn_index': self.cxn_index,
            'component_type': self.component_type,
            'concept_id': self.concept_id,
            'construction': self.construction
        }

class Discourse(Base):
    __tablename__ = 'discourse'
    discourse_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    discourse = Column(String(50))
    index = Column(Integer) 
    isFinalized = Column(Boolean, default=False)
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
            'discourse': self.discourse,
            'isFinalized': self.isFinalized 
        }

# Create tables
Base.metadata.create_all(bind=engine)

def parse_data(file_path):
    lexical_concepts = []
    relational_data = []
    constructions = []
    discourses = []
    current_segment_id = None

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        
        # Handle segment ID markers
        if line.startswith("<sent_id=") or line.startswith("<segment_id="):
            match = re.search(r'<(?:sent_id|segment_id)\s*=\s*([\w_\-]+)>', line)
            if match:
                current_segment_id = match.group(1)
            else:
                current_segment_id = None
        elif line.startswith("</sent_id>") or line.startswith("</segment_id>"):
            current_segment_id = None
        elif line.startswith("#") or line.startswith("%") or line.startswith("*"):
            continue  # Skip comments and markers
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            
            # Parse lexical concepts (minimum 7 parts)
            if len(parts) >= 7:
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

            # Parse relational data (minimum 5 parts)
            if len(parts) >= 5:
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

                    is_main = head_relation.strip() == "0:main"
                    
                    relational_data.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'head_relation': head_relation,
                        'head_index': head_index,
                        'dep_relation': dep_relation,
                        'is_main': is_main
                    })
                except (ValueError, IndexError):
                    pass

            # Parse constructions (minimum 9 parts)
            if len(parts) >= 9:
                try:
                    index = int(parts[1])
                    construction = parts[8]

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
                except (ValueError, IndexError):
                    pass

            # Parse discourse (minimum 6 parts)
            if len(parts) >= 6:
                try:
                    index = int(parts[1])
                    discourse = parts[5]

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
                except (ValueError, IndexError):
                    pass

    return {
        'lexical_concepts': lexical_concepts,
        'relational_data': relational_data,
        'constructions': constructions,
        'discourses': discourses
    }

def insert_lexical_concepts(session, data, chapter_id):
    try:
        for segment_data in data['lexical_concepts']:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_data['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()

            if segment:
                existing_lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index']
                ).first()

                if not existing_lexical_concept:
                    lexical_concept = LexicalConceptual(
                        segment_id=segment.segment_id,
                        segment_index=segment_data['segment_id'],
                        index=segment_data['index'],
                        concept=segment_data['concept'],
                        semantic_category=segment_data['semantic_category'],
                        morpho_semantics=segment_data['morpho_semantics'],
                        speakers_view=segment_data['speakers_view']
                    )
                    session.add(lexical_concept)
            else:
                print(f"LexicalConcept: No segment found for {segment_data['segment_id']}")

        session.commit()
        print("Lexical concepts inserted successfully!")
    except Exception as e:
        print(f"Error inserting lexical concepts: {e}")
        session.rollback()
        raise

def insert_relational_data(session, data, chapter_id):
    try:
        for segment_data in data['relational_data']:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_data['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()
            
            if segment:
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=segment_data['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                existing_relational_entry = session.query(Relational).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index']
                ).first()

                if not existing_relational_entry:
                    relational_entry = Relational(
                        segment_id=segment.segment_id,
                        segment_index=segment_data['segment_id'],
                        index=segment_data['index'],
                        head_index=segment_data['head_index'],
                        dep_relation=segment_data['dep_relation'],
                        head_relation=segment_data['head_relation'],
                        is_main=segment_data['is_main'],
                        concept_id=concept_id
                    )
                    session.add(relational_entry)
            else:
                print(f"Relational: No segment found for {segment_data['segment_id']}")

        session.commit()
        print("Relational data inserted successfully!")
    except Exception as e:
        print(f"Error inserting relational data: {e}")
        session.rollback()
        raise

def insert_construction_data(session, data, chapter_id):
    try:
        for construction_data_item in data['constructions']:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == construction_data_item['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()
            
            if segment:
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=construction_data_item['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                existing_construction_entry = session.query(Construction).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=construction_data_item['segment_id'],
                    index=construction_data_item['index']
                ).first()

                if not existing_construction_entry:
                    construction = Construction(
                        segment_id=segment.segment_id,
                        segment_index=construction_data_item['segment_id'],
                        index=construction_data_item['index'],
                        cxn_index=construction_data_item['cxn_index'],
                        component_type=construction_data_item['component_type'],
                        concept_id=concept_id,
                        construction=construction_data_item['construction']
                    )
                    session.add(construction)
            else:
                print(f"Construction: No segment found for {construction_data_item['segment_id']}")

        session.commit()
        print("Construction data inserted successfully!")
    except Exception as e:
        print(f"Error inserting construction data: {e}")
        session.rollback()
        raise

def insert_discourse_data(session, data, chapter_id):
    try:
        for discourse_data_item in data['discourses']:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == discourse_data_item['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()

            if segment:
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=discourse_data_item['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                existing_discourse_entry = session.query(Discourse).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=discourse_data_item['segment_id'],
                    index=discourse_data_item['index']
                ).first()

                if not existing_discourse_entry:
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
                print(f"Discourse: No segment found for {discourse_data_item['segment_id']}")

        session.commit()
        print("Discourse data inserted successfully!")
    except Exception as e:
        print(f"Error inserting discourse data: {e}")
        session.rollback()
        raise

def insert_all_data(file_path, chapter_id):
    session = SessionLocal()
    try:
        # Parse the data file once
        data = parse_data(file_path)
        
        # Insert data in the correct order
        insert_lexical_concepts(session, data, chapter_id)
        insert_relational_data(session, data, chapter_id)
        insert_construction_data(session, data, chapter_id)
        insert_discourse_data(session, data, chapter_id)
        
        print("All data inserted successfully!")
    except Exception as e:
        print(f"Error during data insertion: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/Aug14_2ch/eng_usr_1.txt"
    chapter_id = 95
    insert_all_data(file_path, chapter_id)

if __name__ == "__main__":
    main()