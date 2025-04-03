import re
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Database configuration
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models (kept consistent with your existing models)
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
    construction = relationship("Construction", back_populates="segment")
    discourse = relationship("Discourse", back_populates="segment")

class LexicalConceptual(Base):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    index = Column(Integer, nullable=False)
    concept = Column(String(255), nullable=False)
    semantic_category = Column(String(255))
    morpho_semantics = Column(String(255))
    speakers_view = Column(String(255))
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

class Construction(Base):
    __tablename__ = 'construction'
    construction_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
    segment_index = Column(String(50), nullable=False)
    index = Column(Integer)
    cxn_index = Column(String(50))
    component_type = Column(String(255))
    concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)
    construction = Column(String(50), nullable=False)
    segment = relationship('Segment', back_populates='construction')
    concept = relationship('LexicalConceptual', back_populates='constructions')

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

# Create tables
Base.metadata.create_all(bind=engine)

def parse_lexical_concepts(file_path):
    lexical_concepts = []
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
        elif line.startswith("#") or line.startswith("%"):
            continue
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            
            if len(parts) >= 7:
                try:
                    index = int(parts[1])
                    concept = parts[0]
                    semantic_category = parts[2]
                    morpho_semantics = parts[3]
                    speakers_view = parts[6]
                    
                    lexical_concepts.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'concept': concept,
                        'semantic_category': semantic_category,
                        'morpho_semantics': morpho_semantics,
                        'speakers_view': speakers_view
                    })
                except ValueError:
                    print(f"Error parsing line: {line}")

    return lexical_concepts

def parse_construction_data(file_path):
    constructions = []
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
            continue
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
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
                except ValueError:
                    print(f"Error parsing line: {line}")

    return constructions

def parse_relational_data(file_path):
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
            continue
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            if len(parts) >= 5:
                try:
                    index = int(parts[1])
                    head_relation = parts[4]
                    
                    if ':' in head_relation:
                        head_index, dep_relation = head_relation.split(':', 1)
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
                except ValueError:
                    pass

    return relational_data

def parse_discourse_data(file_path):
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
            continue
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
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
                except ValueError:
                    print(f"Error parsing line: {line}")

    return discourses

def insert_data(session, file_path, chapter_id):
    try:
        # 1. Lexical Conceptual Data
        lexical_data = parse_lexical_concepts(file_path)
        for segment_data in lexical_data:
            # Find the segment using the segment_index and chapter_id
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_data['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()
            
            if segment:
                # Check if lexical concept already exists
                existing_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index']
                ).first()

                if existing_concept:
                    print(f"Skipping lexical concept: Already exists for segment {segment_data['segment_id']}")
                    continue

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

        # 2. Construction Data
        construction_data = parse_construction_data(file_path)
        for construction_item in construction_data:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == construction_item['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()

            if segment:
                # Find the lexical_conceptual_id
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=construction_item['index']
                ).first()

                # Check if construction already exists
                existing_construction = session.query(Construction).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=construction_item['segment_id']
                ).first()

                if existing_construction:
                    print(f"Skipping construction: Already exists for segment {construction_item['segment_id']}")
                    continue

                construction = Construction(
                    segment_id=segment.segment_id,
                    segment_index=construction_item['segment_id'],
                    index=construction_item['index'],
                    cxn_index=construction_item['cxn_index'],
                    component_type=construction_item['component_type'],
                    concept_id=lexical_concept.lexical_conceptual_id if lexical_concept else None,
                    construction=construction_item['construction']
                )
                session.add(construction)

        # 3. Relational Data
        relational_data = parse_relational_data(file_path)
        for segment_data in relational_data:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == segment_data['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()
            
            if segment:
                # Find the lexical_conceptual_id
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=segment_data['index']
                ).first()

                # Check if relational entry already exists
                existing_relational = session.query(Relational).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id']
                ).first()

                if existing_relational:
                    print(f"Skipping relational data: Already exists for segment {segment_data['segment_id']}")
                    continue

                relational_entry = Relational(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index'],
                    head_index=segment_data['head_index'],
                    dep_relation=segment_data['dep_relation'],
                    head_relation=segment_data['head_relation'],
                    is_main=segment_data['is_main'],
                    concept_id=lexical_concept.lexical_conceptual_id if lexical_concept else None
                )
                session.add(relational_entry)

        # 4. Discourse Data
        discourse_data = parse_discourse_data(file_path)
        for discourse_item in discourse_data:
            segment = session.query(Segment).join(Sentence).filter(
                Segment.segment_index == discourse_item['segment_id'],
                Sentence.chapter_id == chapter_id
            ).first()

            if segment:
                # Find the lexical_conceptual_id
                lexical_concept = session.query(LexicalConceptual).filter_by(
                    segment_id=segment.segment_id,
                    index=discourse_item['index']
                ).first()

                # Check if discourse entry already exists
                existing_discourse = session.query(Discourse).filter_by(
                    segment_id=segment.segment_id,
                    segment_index=discourse_item['segment_id']
                ).first()

                if existing_discourse:
                    print(f"Skipping discourse data: Already exists for segment {discourse_item['segment_id']}")
                    continue

                discourse = Discourse(
                    segment_id=segment.segment_id,
                    segment_index=discourse_item['segment_id'],
                    index=discourse_item['index'],
                    head_index=discourse_item['head_index'],
                    relation=discourse_item['relation'],
                    concept_id=lexical_concept.lexical_conceptual_id if lexical_concept else None,
                    discourse=discourse_item['discourse']
                )
                session.add(discourse)

        session.commit()
        print("All data inserted successfully!")

    except Exception as e:
        print(f"Error inserting data: {e}")
        session.rollback()

    finally:
        session.close()
        print("Processing complete.")

def main():
    # File path for input data
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/health_data_part_2/USRs.txt"
    
    # Specify the chapter_id
    chapter_id = 19

    # Create a session
    session = SessionLocal()

    # Insert data
    insert_data(session, file_path, chapter_id)

if __name__ == "__main__":
    main()

import re

data = {
    "message": """<sent_id=Geo_ncert_11stnd_3ch-bk1_0041>
#अन्य अप्रत्यक्ष स्रोतों में गुरुत्वाकर्षण , चुंबकीय क्षेत्र , व भूकंप संबंधी क्रियाएँ शामिल हैं ।
anya_1\t1\t-\t-\t3:mod\t-\t-\t-\t-
aprawyakRa_1\t2\t-\t-\t1:mod\t-\t-\t-\t-
srowa_1\t3\t-\tpl\t15:k7\t-\t-\t-\t-
guruwvAkarRaNa_1\t5\t-\t-\t-\t-\t-\t-\t18:op1
cuMbakIya\t7\tmale\t-\t-\t-\t-\t-\t17:begin
kRewra_1\t8\t-\t-\t-\t-\t-\t-\t17:inside
[ne_1]\t17\t-\t-\t-\t-\t-\t-\t18:op2
BUkaMpa_1\t11\t-\t-\t12:mod\t-\t-\t-\t-
saMbaMXI_1\t12\t-\t-\t13:mod\t-\t-\t-\t-
kriyA_1\t13\t-\tpl\t-\t-\t-\t-\t18:op3
SAmila_1\t14\t-\t-\t15:k1s\t-\t-\t-\t-
hE_1-pres\t15\t-\t-\t0:main\t-\t-\t-\t-
[conj_1]\t18\t-\t-\t15:k1\t-\t-\t-\t-
%affirmative
</sent_id>

<sent_id=Geo_ncert_11stnd_6ch-bk1_0284a>
#आर्द्र , उष्ण एवं भूमध्य रेखीय जलवायु में बैक्टेरियल वृद्धि एवं क्रियाएँ सघन होती हैं ।
Arxra_1\t1\t-\t-\t-\t-\t-\t-\t20:op1
uRNa_1\t3\t-\t-\t-\t-\t-\t-\t20:op2
BUmaXya\t5\t-\t-\t-\t-\t-\t-\t17:begin
reKIya_1\t6\t-\t-\t7:mod\t-\t-\t-\t-
jalavAyu_1\t7\t-\t-\t-\t-\t-\t-\t17:inside
[ne_1]\t17\t-\t-\t14:k7\t-\t-\t-\t-
bEkteriyala\t9\t-\t-\t-\t-\t-\t-\t18:begin
vqxXi_1\t10\t-\t-\t-\t-\t-\t-\t18:inside
[ne_2]\t18\t-\t-\t11:ccof\t-\t-\t-\t-
kriyA_1\t12\t-\tpl\t11:ccof\t-\t-\t-\t-
saGana_1\t13\t-\t-\t-\t-\t-\t-\t19:kriyAmUla
ho_1-wA_hE_1\t14\t-\t-\t-\t-\t-\t-\t19:verbalizer
[cp_1]\t19\t-\t-\t-\t-\t-\t-\t20:op3
[conj_1]\t20\t-\t-\t0:main\t-\t-\t-\t-
%affirmative
</sent_id>""",
    "status": "success"
}

# Extract sentences and USR
matches = re.findall(r"(<sent_id=.*?>)\n#(.*?)\n(.*?)\n(</sent_id>)", data["message"], re.DOTALL)

for match in matches:
    sent_start = match[0]
    sentence = match[1]
    usr_structure = match[2]
    sent_end = match[3]

    print(sent_start)  # Keep <sent_id=...>
    print(f"# {sentence}")  # Sentence text with #
    print(usr_structure)  # USR content
    print(sent_end)  # Keep </sent_id>
