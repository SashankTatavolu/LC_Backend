import re
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Database configuration
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sashank123@localhost/testdb"
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
    file_path = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/Ecommerce_data/USRs.txt"
    
    # Specify the chapter_id
    chapter_id = 1

    # Create a session
    session = SessionLocal()

    # Insert data
    insert_data(session, file_path, chapter_id)

if __name__ == "__main__":
    main()

import re

data = {
    "message": """<sent_id=Ecommerce_FAQ_001a>
#खाता बनाने/खोलने के लिए, हमारी वेबसाइट के ऊपरी दाएँ कोने पर स्थित 'साइन अप' बटन पर क्लिक करें ।
$addressee 22 anim - 21:k1 - respect - -
KAwA_1 1 - - 24:k2 - - - -
banA_1 2 - - - - - - 24:op1
Kola_1 23 - - - - - - 24:op2
[disjunct_1] 24 - - 21:rt - - - -
$speaker 5 anim pl 6:r6 - - - -
^vebasAita_1 6 - - 10:r6 - - - -
Upara_1 8 - mawup 10:mod - - - -
xAyAz_1 9 - - 10:mod - - - -
konA_1 10 - pl 27:k7p - - - -
sWiwa_1 27 - kqw 26:mod - - - -
^sAina 12 - - - - - - 25:begin
^apa 13 - - - - - - 25:inside
[ne_1] 25 - - - - - - 26:mod
batana_1 14 - - - - - - 26:head
[6-waw_1] 26 - - 21:k7p - - - -
klika_1 16 - - - - - - 21:kriyAmUla
kara_1-o_1 17 - - - - - - 21:verbalizer
[cp_1] 21 - -  0:main - - - -
%imperative
</sent_id>

<sent_id=Ecommerce_FAQ_001b>
#और पंजीकरण प्रक्रिया को पूरी करने के लिए निर्देशों का पालन करें।
$addressee 16 anim - 15:k1 - respect - -
paMjIkaraNa_1 1 - - - - - - 13:mod
prakriyA_1 2 - - - - - - 13:head
pUrA_1 4 - - - - - - 14:kriyAmUla
kara_1 5 - pl - - - - 14:verbalizer
nirxeSa_1 8 - pl 15:k2 - - - -
pAlana_1 10 - - - - - - 15:kriyAmUla
kara_1-o_1 11 - - - Ecommerce_FAQ_001a.21:samuccaya - - 15:verbalizer
[nc_1] 13 - - 14:k2 - - - -
[cp_1] 14 -  - 15:rt - - - -
[cp_2] 15 - - 0:main - - - -
%imperative
</sent_id>

<sent_id=Ecommerce_FAQ_002>
#हम ऑनलाइन ऑर्डर के लिए भुगतान विधियों के रूप[a][b] में प्रमुख क्रेडिट कार्ड, डेबिट कार्ड और PayPal स्वीकार करते हैं।
$speaker 1 - pl 26:k1 - - - -
^OYnalAina_1 2 - - - - - - 22:mod
^OYrdara_1 3 - - - - - - 22:head
BugawAna_1 6 - - - - - - 23:mod
viXi_1 7 - pl - - - - 23:head
rUpa_1 28 - - 26:k7 - - - -
pramuKa_1 11 - - 27:mod - - - -
^kredita_1 12 - - - - - - 24:mod
^kArda_1 13 - - - - - - 24:head
^debita_1 14 - - - - - - 25:mod
^kArda_1 15 - - - - - - 25:head
^PayPal 17 - - - - - - 27:op3
svIkAra_1 18 - - - - - - 26:kriyAmUla
kara_1-wA_hE_1 19 - - - - - - 26:verbalizer
[6-waw_1] 22 - - 27:rt - - - -
[6-waw_2] 23 - - 28:r6 - - - -
[4-waw_1] 24 - - - - - - 27:op1
[4-waw_2] 25 - - - - - - 27:op2
[cp_1] 26 - - 0:main - - - -
[conj_1] 27 - - 26:k2 - - - -
%affirmative
</sent_id>

<sent_id=Ecommerce_FAQ_003>
#आप अपने खाते में लॉग इन करके और 'ऑर्डर इतिहास' अनुभाग पर जाकर अपने ऑर्डर को ट्रैक कर सकते हैं।
$addressee 1 anim - 23:k1 - respect - -
apanA 2 - pl 3:r6 1:coref - - -
KAwA_1 3 - pl 27:k7p - - - -
^lOYga+ina_1 5 - - - - - - 27:kriyAmUla
kara_1 7 - - - - - - 27:verbalizer
[cp_2] 27 - - - - - - 25:op1
^OYrdara_1 9 - - - - - - 22:mod
iwihAsa_1 10 - - - - - - 22:head
anuBAga_1 11 - - - - - - 28:head
jA_1 13 - - - - - - 25:op2
apanA_1 14 - pl 15:r6 - - - -
^OYrdara_1 15 - - 23:k2 - - - -
^trEka_1 17 - - - - - - 23:kriyAmUla
kara_1-0_sakawA_hE_1 18 - - - - - - 23:verbalizer
[karmaXAraya_1] 22 - - - - - - 28:mod
[6-waw_1] 28 - - 23:k7p - - - -
[cp_1] 23 - - 0:main - - - -
[conj_1] 25 - - 23:rpk - - - -
%affirmative
</sent_id>

<sent_id=Ecommerce_FAQ_004>
#वहाँ, आपको अपने शिपमेंट की ट्रैकिंग की जानकारी मिलेगी।
$wyax 1 - - 8:k7p Ecommerce_FAQ_003.28:coref distal - -
$addressee 2 anim - 8:k4 - respect  - -
apanA 3 - pl 4:r6 2:coref - - -
^SipameMta_1 4 - - 6:r6 - - - -
^trEkiMga_1 6 - - 7:r6 - - - -
jAnakArI_1 7 - - 8:k1 - - - -
mila_1-gA_1 8 - - 0:main - - - - 
%affirmative
</sent_id>

<sent_id=Ecommerce_FAQ_005a>
#हमारी वापसी नीति आपको पूर्ण धनवापसी के लिए खरीददारी के 30 दिनों के भीतर उत्पाद वापस करने की अनुमति देती है।
$speaker 1 - pl 23:r6 - - - -
vApasI_1 2 - - - - - - 23:mod
nIwi_1 3 - - - - - - 23:head
$addressee 4 anim - 25:k4 - respect  - -
pUrNa_1 5 - - 6:mod - - - -
XanavApasI_1 6 - - 25:rt - - - -
KarIxaxArI_1 9 - - 12:r6 - - - -
30 11 numex - 12:card - - - -
xina_1 12 - pl 24:dur - - - -
uwpAxa_1 15 - - 24:k2 - - - -
vApasa_1 16 - - - - - - 24:kriyAmUla
kara_1 17 - pl - - - - 24:verbalizer
anumawi_1 19 - - - - - - 25:kriyAmUla
xe_1-wA_hE_1 20 - - - - - - 25:verbalizer
[6-waw_1] 23 - - 25:k1 - - - -
[cp_1] 24 - - 25:k2 - - - -
[cp_2] 25 - - 0:main - - - -
%affirmative
</sent_id>

<sent_id=Ecommerce_FAQ_005b>
#बशर्ते[c][d] वे अपनी मूल स्थिति और पैकेजिंग में हों।
$wyax 2 - pl 9:k1 Ecommerce_FAQ_005a.15:coref distal - -
apanA 3 - - 11:r6 2:coref - - -
mUla_1 4 - - 5:mod - - - -
sWiwi_1 5 - - - - - - 11:op1
^pEkejiMga_1 7 - - - - - - 11:op2
hE_1-e_[g][h] 9 - - 0:main - Ecommerce_FAQ_005a.25:AvaSyakawApariNAma - -
[conj_1] 11 - - 9:k7 - - - -
%affirmative
</sent_id>

<sent_id=Ecommerce_FAQ_006>
#विस्तृत निर्देशों के लिए कृपया हमारे रिटर्न पेज को देखें।
$addressee 13 anim - 10:k1 - respect  - -
viswqwa_1 1 - - 2:mod - - - -
nirxeSa_1 2 - pl 10:rt - - - -
kqpayA_1 5 - - 10:vkvn - - - -
$speaker 6 - pl 12:r6 - - - -
^ritarna_1 7 - - - - - - 12:mod
^peja_1 8 - - - - - - 12:head
xeKa_1-o_1 10 - - 0:main - - - -
[nc_1] 12 - - 10:k2 - - - -
%imperative 
</sent_id>

<sent_id=Ecommerce_FAQ_007a>
#आपका ऑर्डर अभी तक शिप नहीं हुआ है ।
$addressee 1 - - 2:r6 - respect  - -
^OYrdara_1 2 - - 7:k1 - - - -
aBI_1 3 - - - - - - 8:end
^Sipa_1 5 - - - - - - 7:kriyAmUla
nahIM_1 6 - - 7:neg - - - -
ho_1-yA_hE_1 9 - - - - - - 7:verbalizer
[cp_1] 7 - - 0:main - - - -
[span_1] 8 - - 7:k7t - - - -
%negative
</sent_id>
<sent_id=Ecommerce_FAQ_007b>
#तो आप अपना ऑर्डर रद्द कर सकते हैं।
$addressee 1 anim - 9:k1 - respect  - -
apanA 2 - - 3:r6 1:coref - - -
^OYrdara_1 3 - - 9:k2 - - - -
raxxa_1 4 - - - - - - 9:kriyAmUla
kara_1-0_saka[i][j]wA_hE_1 5 - - - - - - 9:verbalizer 
[cp_1] 9 - - 0:main - Ecommerce_FAQ_007a.7:AvaSyakawApariNAma[k][l] - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_008a>
#कृपया अपने ऑर्डर विवरण के साथ हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 19 anim - 17:k1 - respect - - 
kqpayA_1    1    -    -    17:vkvn   -    -    -    -
apanA    2    -    -    15:r6   19:coref    -    -    -
^OYrdara_1    3    -    -    -    -    -    -    15:mod
vivaraNa_1    4    -    -     -    -    -   -   15:head
[nc_1]    15    -    -    17:rask1    -     -    -    -
$speaker    7    anim    pl    18:r6    -    -    -    -
grAhaka_1    8    -    -    -  -    -    -    16:mod
sahAyawA_1    9    -    -     -  -    -    -    16:head
[nc_2]    16    -    -    -   -    -    -    18:mod
tIma_1    10    -    -    -   -    -    -    18:head
[nc_3]    18    -    -    17:k2    -    -    -    -
saMparka_1    12    -    -    -   -    -    -    17:kriyAmUla
kara_1-o_1   13    -    -   -   -    -    -    17:verbalizer
[cp_1]    17    -    -    0:main   -    -    -    -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_008b>
#और हम रद्दीकरण प्रक्रिया में आपकी सहायता करेंगे।
$speaker 1 anim pl 10:k1 - - - -
raxxIkaraNa_1 2 - - - - - - 9:mod
prakriyA_1 3 - - - - - - 9:head
$addressee 5 anim - 10:k2 - respect - -
sahAyawA_1 6 - - - - - - 10:kriyAmUla
kara_1-gA_1 7 - - - - - - 10:verbalizer
[6-waw_1] 9 - - 10:k7 - - - -
[cp_1] 10 - - 0:main Ecommerce_FAQ_008a.17:samuccaya - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_009>
#शिपिंग का समय गंतव्य और चुनी गई शिपिंग विधि के आधार पर अलग-अलग होता है।
^SipiMga_1 1 - - 3:r6 - - - -
samaya_1 3 - - 14:k1 - - - -
gaMwavya_1 4 - - - - - - 20:op1
cuna_1 6 - -  17:rbks - - - -
^SipiMga_1 8 - - - - - - 17:mod
viXi_1 19 - - - - - - 17:head
alaga_1 13 - xviwva  3:k1s - - - -
ho_1-wA_hE_1 14 - - 0:main - - - -
[6-waw_1] 17 - - - - - - 20:op2
[conj_1] 20 - - 14:k7  - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_010a>
#मानक शिपिंग में आमतौर पर 3-5 व्यावसायिक दिन लगते हैं।
mAnaka_1 1 - - 2:mod - - - -
^SipiMga_1 2 - - 9:rt - - - -
AmawOra+para_1 4 - - 9:krvn - - - -
3 6 numex - - - - - 11:start
5 10 numex  - - - - - 11:end
vyAvasAyika_1 7 - - 8:mod - - - -
xina_1 8 - - 9:k1 - - - -
laga_1-wA_hE_1 9 - - 0:main - - - -
[span_1] 11 - - 7:card - - -        -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_010b>
#जबकि एक्सप्रेस शिपिंग में 1-2 व्यावसायिक दिन लग सकते हैं।
^eksapresa_1 1 - - 2:mod - - - -
^SipiMga_1 2 - - 7:k7 - - - -
1 4 numex - - - - - 13:start
2        12        numex        -        -        -        -        -        13:end
[span_1]        13        -        -        6:card        -        -        -        -
vyAvasAyika_1 5 - - 6:mod - - - -
xina_1 6 - - 7:k1  - - - -
laga_1-0_sakawA_hE_1 7 - - 0:main Ecommerce_FAQ_010a.9:viroXI_xyowaka - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_011>
#हाँ, हम चुनिंदा देशों में अंतर्राष्ट्रीय शिपिंग प्रदान करते हैं।
$speaker 2 anim pl 12:k1 - - - -
cuniMxA_1 3 - - 4:mod - - - -
xeSa_1 4 - pl 12:k7p - - - -
aMwarrARtrIya_1 6 - - 7:mod - - - -
^SipiMga_1 7 - - 12:k2 - - - -
praxAna_1 8 - - - - - - 12:kriyAmUla
kara_1-wA_hE_1 9 - - - - - - 12:verbalizer
[cp_1] 12 - - 0:main - hAz_1 - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_012>
#उपलब्धता और शिपिंग लागत की गणना आपके स्थान के आधार पर चेकआउट प्रक्रिया के दौरान की जाएगी।
upalabXawA_1 1 - - - - - - 21:op1
^SipiMga_1 3 - - - - - - 19:mod
lAgawa_1 4 - - - - - - 19:head
[6-waw_1] 19 - - - - - - 21:op2
$addressee 7 anim - 8:r6 - respect - -
sWAna_1 8 - - 16:k7 - - - -
^cekaAuta_1 12 - - - - - - 20:mod
prakriyA_1 13 - - - - - - 20:head
[6-waw_2] 20 - - 16:k7t - - - -
gaNanA_1 6 - - - - - - 16:kriyAmUla
kara_1-yA_jA_gA_1 17 - - - - - - 16:verbalizer
[cp_1] 16 - - 0:main - - - -
[conj_1] 21 - - 16:k2 - - - -
%pass_affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_013a>
#आपका पैकेज ट्रांज़िट के दौरान खो गया है ।
$addressee 1 anim - 2:r6 - respect - -
^pEkeja_1 2 - - 6:k1 - - - -
^trAMjZita_1 3 - - 6:k7t - - - -
Ko_1-yA_hE_1 6 - - 0:main Ecommerce_FAQ_013c.6:AvaSyakawApariNAma [shade:jA_1] - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_013b>
#या वह क्षतिग्रस्त हो गया है ।
$wyax 1 - - 3:k1 Ecommerce_FAQ_013a.2:coref distal - -
kRawigraswa_1 2 - - 3:k1s - - - -
ho_1-yA_hE_1 3 - - 0:main Ecommerce_FAQ_013a.3:anyawra [o][shade:jA_1] - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_013c>[q]
#तो कृपया तुरंत हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 13 anim - 20:k1 -[r][s] respect - - 
kqpayA_1 1 - - 20:vkvn - - - -
wuraMwa_1 2 - - 9:krvn - - - -
$speaker 3 anim pl 20:k1 - - - -
grAhaka_1 4 - - - - - - 11:mod
sahAyawA_1 5 - - - - - - 11:head
[6-waw_1] 11 - - - - - - 12:mod 
^tIma_1 6 - - - - - - 12:head
[4-waw_1] 12 - - 9:k2 - - - -  
saMparka_1 8 - - - - - - 20:kriyAmUla
kara_1-o_[v][w]1 9 - - - - - - 20:verbalizer
[cp_1]  20 - - 0:main - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_014a>
#हम जांच शुरू करेंगे ।
$speaker 1 anim pl 6:k1 - - - -
jAMca_1 2 - - 6:k2 - - - -
SurU_1 3 - - - - - - 6:kriyAmUla
kara_1-gA_1 4 - - - - - - 6:verbalizer
[cp_1] 6 - - 0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_014b>
#और हम समस्या को हल करने के लिए आवश्यक कदम उठाएंगे।
$speaker 1 anim pl 13:k1 - - - -
samasyA_1 2 - - 12:k2 - - - -
hala_1 4 - - - - - - 12:kriyAmUla
kara_1 5 - pl - - - - 12:verbalizer
AvaSyaka_1 8 - - 13:krvn - - - -
kaxama_1 9 - - - - - - 13:kriyAmUla
uTA_1-gA_1 10 - - - Ecommerce_FAQ_014a.6:samuccaya - - 13:verbalizer
[cp_1] 12 - - 13:rt - - - -
[cp_2] 13 - - 0:main - - - -
%affirmative
</sent_id>

<sent_id=Ecommerce_FAQ_015a>
#आपको अपना शिपिंग पता बदलने की आवश्यकता है।
$addressee 1 anim - 8:k4a - respect - -
apanA 2 -  - 10:r6 [ab][ac]1:coref - - -
^SipiMga_1 3 - - - - - - 10:mod
pawA_1 4 - - - - - - 10:head
baxala_1 5 - pl 7:r6 - - - -
AvaSyakawA_1 7 - - 8:k1 - - - -
hE_1-pres 8 - - 0:main Ecommerce_FAQ_015b.8:AvaSyakawApariNAma - - -
[6-waw_1] 10 - - 5:k2 - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_015b>
#तो कृपया तुरन्त हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 16 anim - 14:k1 - respect - - 
kqpayA_1 1 - - 14:vkvn - - - -
wuranwa_1 2 - xviwva  14:krvn - - - -
$speaker 5 anim pl 15:r6 [ad][ae]- - - -
grAhaka_1 6 - - - - - - 13:mod
sahAyawA_1 7 - - - - - - 13:head
tIma_1 8 - - - - - - 15:head
saMparka_1 10 - - - - - - 14:kriyAmUla
kara_1-o_1[af][ag] 11 - - - - - - 14:verbalizer
[nc_1] 13 - - - - - - 15:mod
[nc_2] 15 - - 14:k2 - - - -
[cp_1] 14 - - 0:main - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_016a>
#ऑर्डर अभी तक शिप नहीं किया गया है ।
^OYrdara_1 1 - - 10:k2 - - - -
aBI_1 2 - - - - - - 11:end
[span_1] 11 - - 10:k7t - - - - 
^Sipa_1 4 - - - - - - 10:kriyAmUla
nahIM_1 5 - - 10:neg - - - -
kara_1-yA_jA_yA_hE_1 6 - - - - - - 10:verbalizer
[cp_1] 10 - - 0:main - - - -
%pass_negative
</sent_id>
<sent_id=Ecommerce_FAQ_016b>
#तो हम पता अपडेट करने की पूरी कोशिश करेंगे।
$speaker 1 anim pl 11:k1 - - - -
pawA_1 2 - - 10:k2 - - - -
^apadeta_1 3 - - - - - - 10:kriyAmUla
kara_1 4 - pl - - - - 10:verbalizer
pUrA_1 6 - - 11:krvn - - - -
koSiSa_1 7 - - - - - - 11:kriyAmUla
kara_1-gA_1 8 - - - - - - 11:verbalizer
[cp_1] 10 - - 11:k2 - - - -
[cp_2] 11 - - 0:main - Ecommerce_FAQ_016a,10:AvaSyakawApariNAma - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_017>
#आप हमारी ग्राहक सहायता टीम से फ़ोन नंबर पर फ़ोन करके या ईमेल पते पर ईमेल करके संपर्क कर सकते हैं।
$addressee 1 anim - 27:k1 - respect - -
$speaker 2 anim pl 24:r6 - - - -
grAhaka_1 3 - - - - - - 23:mod
sahAyawA_1 4 - - - - - - 23:head
[6-waw_1] 23 - - - - - - 24:mod
^tIma_1 5 - - - - - - 24:head
[4-waw_1] 24 - - 27:k2 - - - - 
^PZona_1 7 - - - - - - 29:mod
naMbara_1 8 - - - - - - 29:head
[6-waw_2] 29 - - 25:k7p - - - -  
^PZona_1 10 - - - - - - 25:kriyAmUla
kara_1 11 - - - - - - 25:verbalizer
[cp_1] 25 - - - - - - 28:op1 
^Imela_1 13 - - - - - - 30:mod
pawA_1 14 - - - - - - 30:head
[6-waw_3] 30 - - 26:k7p - - - -   
^Imela_1 16 - - - - - - 26:kriyAmUla
kara_1 17 - - - - - - 26:verbalizer
[cp_2] 26 - - - - - - 28:op2
saMparka_1 18 - - - - - - 27:kriyAmUla
kara_1-0_sakawA_hE_1 19 - - - - - - 27:verbalizer
[cp_3] 27 - - 0:main - - - -
[disjunct_1] 28 - - 27:rpk - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_018>
#हमारी टीम आपकी किसी भी पूछताछ या समस्या में सहायता करने के लिए कार्य समय के दौरान उपलब्ध है।
$speaker 1 anim pl 2:r6 - - - -
^tIma_1 2 - - 17:k1 - - - -
$addressee 3 anim - 6:r6 - respect - -
koI_1 4 - - 21:quant - BI_6 - -
pUCawACa_1 6 - - - - - - 21:op1
samasyA_1 8 - - 11:k7 - - - [ak][al][am]-
sahAyawA_1 10 - - - - - - 21:op2
kara_1 11 - pl - - - - 20:verbalizer[an]
kArya_1 14 - - - - - - 19:mod
samaya_1 15 - - - - - - 19:head
upalabXa_1 16 - - 17:k1s - - - -
hE_1-pres 17 - - 0:main - - - -
[6-waw_1] 19 - - 17:k7t - - - -
[cp_1] 20 - - 17:rt - - - -
[disjunct_1] 21 - - - - - - 20:kriyAmUla
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_019>
#हाँ, हम अतिरिक्त शुल्क लेकर उपहार रैपिंग सेवाएँ प्रदान करते हैं।
$speaker 2 anim pl 15:k1 - - - -
awirikwa_1 3 - - 4:mod - - - -
Sulka_1 4 - - 17:k2 - - - -
le_1 17 - - 15:rpk - - - -
upahAra_1 7 - - - - - - 14:mod
^rEpiMga_1 8 - - - - - - 14:head[aq][ar]
[4-waw_1] 14 - - - - - - 16:mod 
sevA_1 9 - pl - - - - 16:head
[6-waw_1][as][at] 16 - - 15:k2 - - - - 
praxAna_1 10 - - - - - - 15:kriyAmUla
kara_1-wA_hE_1 11 - - - - - - 15:verbalizer
[cp_1] 15 - - 0:main - hAz[au][av]_1 - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_020>
#चेकआउट प्रक्रिया के दौरान, आप अपने ऑर्डर में उपहार रैपिंग जोड़ने का विकल्प चुन सकते हैं।
^cekaAuta_1 1 - - - - - - 18:mod
prakriyA_1 2 - - 14:k3 - - - 18:head
[6-waw_1] 18 - - 14:k7t - - - - 
$addressee 5 anim - 14:k1 - respect - -
apanA 6 - pl 7:r6 5:coref - - -
^OYrdara_1 7 - - 11:k7 - - - -
upahAra_1 9 - - - - - - 19:mod
rEpiMga_1 10 - - - - - - 19:head
[4-waw_1] 19 - - 11:k2 - - - -  
jodZa_1 11 - - 13:r6 - - - -
vikalpa_1 13 - - 14:k2 - - - -
cuna_1-0_sakawA_hE_1 14 - - 0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_021>[ay]
#हमारे पास एक मूल्य मिलान नीति है, जिसके तहत हम प्रतिस्पर्धी की वेबसाइट पर पाए जाने वाले समान उत्पाद की कीमत का मिलान करेंगे।
$speaker 1 - pl 7:rsm - - - -
1 3 - numex 6:card - - - -
mUlya_1 4 - - - - - - 26:mod
milAna_1 5 - - - - - - 26:head
nIwi_1 6 - - - - - - 28:head
hE_1-pres 7 - - 0:main - - - -
$yax 8 - - 30:k7a 28:coref - - -
$speaker 10 - pl 30:k1 - - - -
prawisparXI_1 11 - - 13:r6 - - - -
^vebasAita_1 13 - - 30:k7 - - - -
pA_1 15 - - 19:mod - - - -
samAna_1 18 - - 19:mod - - - -
uwpAxa_1 19 - - 21:r6 - - - -
kImawa_1 21 - - 30:k2 - - - -
milAna_1 23 - - - - - - 30:kriyAmUla
kara_1-gA_1 24 - - - - - - 30:verbalizer
[6-waw_1] 26 - - - - - - 28:mod
[4-waw_1] 28 - - 7:k7 - - - -
[cp_2] 30 - - 28:rcelab - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_022>
#कृपया उत्पाद के विवरण और प्रतिस्पर्धी के ऑफ़र के साथ हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 23 - - 20:k1 - respect  - -
kqpayA_1 1 - - 20:vkvn - - - -
uwpAxa_1 2 - - 4:r6 - - - -
vivaraNa_1 4 - - - - - - 21:op1
prawisparXI_1 6 - - 8:r6 - - - -
^OYPZara_1 8 - - - - - - 21:op2[az][ba]
$speaker 11 - pl 14:r6 - - - -
grAhaka_1 12 - - - - - - 19:mod
sahAyawA_1 13 - - - - - - 19:head
^tIma_1 14 - - - - - - 22:head
saMparka_1 16 - - - - - - 20:kriyAmUla[bb][bc]
kara_1-o_1 17 - - - - - - 20:verbalizer[bd][be]
[6-waw_1] 19 - - - - - - 22:mod
[4-waw_1] 22 - - 20:k2 -[bh][bi] - - -
[cp_1] 20 - - 0:main - - - -
[conj_1] 21 - - 23:rask3 - - -  -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_023>[bl]
#दुर्भाग्य से, हम फ़ोन पर ऑर्डर स्वीकार नहीं करते हैं।[bm]
xurBAgya+se_1 1 - -  9:rh - - - -
$speaker 3 - pl 9:k1 - - - -
^PZona_1 4 - - 9:k7 - - - -
^OYrdara_1 6 - - 9:k2 - - - -
svIkAra_1 7 - - - - - - 12:kriyAmUla
nahIM_1 8 - - 9:neg - - - -
kara_1-wA_hE_1 9 - - - - - - 12:verbalizer
[cp_1] 12 - - 0:main - - - -
%negative
</sent_id>
<sent_id=Ecommerce_FAQ_024>
#कृपया एक सहज और सुरक्षित लेनदेन के लिए हमारी वेबसाइट के माध्यम से अपना ऑर्डर दें।
$addressee 19 anim - 16:k1 - respect  - -
kqpayA[bo][bp]_1 1 - - 16:vkvn - - - -
eka_2 2 - - 6:quant - - - -
sahaja_1 3 - - - - - - 18:op1
surakRiwa_1 5 - - - - - - 18:op2
lenaxena_1 6 - - 16:rt [bs]- - - -
$speaker 9 - pl 10:r6 - - - -
^vebasAita_1 10 - - 16:k3 - - - -
apanA 14 - - 15:r6 19:coref - - - 
^OYrdara_1 15 - - 16:k2 - - - -
xe_1-o_1 16 - - 0:main - - - -
[conj_1] 18 - - 6:mod - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_025>
#हाँ, हम आपकी व्यक्तिगत जानकारी और भुगतान की जानकारी की सुरक्षा को गंभीरता से लेते हैं।
$speaker 2 - pl 13:k1 - - - -
$addressee 3 anim - 9:r6 - respect  - -
vyakwigawa_1 4 - - 18:mod -[bt][bu] - - -
jAnakArI_1 18 - - - - - - 16:op1
BugawAna_1 6 - - 7:r6 - - - -[bv]
jAnakArI_1 7 - - - - - - 16:op2
surakRA_1 9 - - 13:k2 - - - -
gaMBIrawA_1 11 - - 13:krvn - - - -
le_1-wA_hE_1 13 - - 0:main -  hAz_1 - -
[conj_1] 16 - - 9:r6 - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_026a>  
#हम उद्योग-मानक एन्क्रिप्शन का उपयोग करते हैं ।[bw]
$speaker 1 anim pl 10:k1 - - - -
uxyoga_1 12 - - - - - - 9:mod
mAnaka_1 13 - - - - - - 9:head
^enkripSana_1 3 - - - - - - 11:head
upayoga_1 5 - - - - - - 10:kriyAmUla
kara_1-wA_hE_1 6 - - - - - - 10:verbalizer
[6-waw_1] 9 - - - - - - 11:mod
[6-waw_2] 11 - - 10:k2 - - - -
[cp_1] 10 - - 0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_026b>
#और हम आपकी जानकारी की सुरक्षा सुनिश्चित करने के लिए सख्त सुरक्षा प्रोटोकॉल का पालन करते हैं।
$speaker 1 - pl 20:k1 - - - -
$addressee 2 - - 3:r6 - respect  - -
jAnakArI_1 3 - - 5:r6 - - - -
surakRA_1 5 - - 19:k2 - - - -
suniSciwa_1 6 - - - - - - 19:kriyAmUla
kara_1 7 - pl - - - - 19:verblizer
saKwa_1 10 - - 18:mod - - - 21:mod
surakRA_1 11 - - - - - - 21:head
[karmaXAraya_1] 21 - - - - - - 18:mod
^protokOYla_1 12 - - 21:r6 - - - 18:head
pAlana_1 14 - - - - - - 20:kriyAmUla
kara_1-wA_hE_1 15 - - - - - - 20:verbalizer
[6-waw_1] 18 - - 20:k2 - - - -
[cp_1] 19 - - 20:rt - - - -
[cp_2] 20 - - 0:main Ecommerce_FAQ_026a.10:samuccaya - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_027a>
#आपके द्वारा खरीदा गया कोई उत्पाद आपकी खरीद के 7 दिनों के भीतर सेल पर चला जाता है ।
$addressee 1 - - 3:k3 - respect - -
KarIxa_1 3 - - 16:rbks - - - -
koI[by] 5 - - 6:mod [bz]- - - -
uwpAxa_1 6 - - 16:k1 - - - -[ca]
$addressee 7 - - 8:r6 - respect  - -
KarIxa_1 8 - - 11:r6 - - - -
7 10 numex - - - - - 17:count
xina_1 11 - pl - - - - 17:unit
[span_1] 17 - - 16:k7t - - - -
BIwara_1[cc] 13 - - 11:rkl - - - -
sela_1 14 - - 16:k7 - - - -
calA_1-yA_jA_wA_hE_1 16 - - 0:main - - - -
%pass_affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_027b>
#तो हम एक बार मूल्य समायोजन प्रदान करते हैं।
$speaker 1 - pl 7:k1 - - - -
eka+bAra_1  2 - - 11:krvn -[ce] - - -
mUlya_1 4 - - - - - - 10:mod
samAyojana_1 5 - - - - - - 10:head
praxAna_1 6 - - - - - - 11:kriyAmUla
kara_1-wA_hE_1 7 - - - - - - 11:verbalizer
[6-waw_1] 10 - - 11:k2 - - - -
[cp_1] 11 - - 0:main - Ecommerce_FAQ_027a.16:AvaSyakawApariNAma - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_028>
#समायोजन का अनुरोध करने के लिए कृपया अपने ऑर्डर विवरण के साथ हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 26 - - 24:k1 - respect  - -
samAyojana_1 1 - - 23:rt - - - -[cf]
anuroXa_1 3 - - - - - - 23:kriyAmUla
kara_1 4 - pl - - - - 23:verblizer
kqpayA[cg] 7 - - 24:vkvn - - - -
apanA 8 - pl 21:r6 25:coref - - -
^OYrdara_1 9 - - - - - - 21:mod
vivaraNa_1 10 - - - - - - 21:head
$speaker 13 - pl 25:r6 - - - -
grAhaka_1 14 - - - - - - 22:mod
sahAyawA_1 15 - - - - - - 22:head
^tIma_1 16 - - - - - - 25:head
saMparka_1 18 - - - - - - 24:kriyAmUla
kara_1-o_1 19 - - - - - - 24:verblizer
[6-waw_1] 21 - - 24:rask1 - - - -
[6-waw_2] 22 - - - - - - 25:mod
[4-waw_1] 25 - - 24:k3 - - - -
[cp_1] 23 - - 24:rt - - - -
[cp_2] 24 - - 0:main - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_029>
#हां, हमारे पास एक लॉयल्टी प्रोग्राम है जहां आप हर खरीद के लिए अंक अर्जित कर सकते हैं।
$speaker 2 - pl 22:rsm - - - -
eka_2 4 - - 22:card - - - -
^lOYyaltI_1 5 - - - - - - 22:mod
progrAma_1 6 - - - - - - 22:head
hE_1-pres 7 - - 0:main - - - -
$yax 8 - - 21:k7p 22:coref - - -
$addressee 9 - - 21:k1 - respect  - -
hara_1 10 - - 11:quant - - - -
KarIxa_1 11 - - 21:rt - - - -
aMka_1 14 - - 21:k2 - - - -
arjiwa_1 15 - - - - - - 21:kriyAmUla
kara_1 16 - pl - - - - 21:verbalizer
[cp_1] 21 - - 22:rcloc - - - -
[2-waw_1] 22  - - 7:k1 - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_030>
#इन अंकों को भविष्य के ऑर्डर पर छूट के लिए भुनाया जा सकता है।
$wyax 1 - pl 2:dem - proximal - -
aMka_1 2 - pl 11:k2 Ecommerce_FAQ_029.14:coref - - -
BaviRya_1 4 - - 6:k7t - - - -
^OYrdara_1 6 - - 11:k7 - - - -
CUta_1 8 - - 11:rt - - - -
BunA_1-yA_jA_sakawA_hE_1 11 - - 0:main - - - -
%pass_affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_031>
#कृपया अधिक जानने और कार्यक्रम में शामिल होने के लिए हमारी वेबसाइट पर जाएं।
$addressee 18 anim - 14:k1 - respect - -
kqpayA_1 1 - - 14:vkn - - - -
aXika_1 2 - - 3:mod - - - -
jAna_1 3 - pl 14:k7 - - - 17:op1
kAryakrama_1 5 - - 16:k7 - - - -
SAmila_1 7 - - - - - - 16:kriyAmUla
ho_1 8 - pl 14:k7 - - - 16:verbalizer
$speaker 11 - pl 12:r6 - - - -
^vebasAita_1 12 - - 14:k7p - - - -
jA_1-e_1 14 - - 0:main - - - -
[cp_1] 16 - - - - - - 17:op2
[conj_1] 17 - - 14:rt - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_032>
#हां, आप खाता बनाए बिना अतिथि के रूप में ऑर्डर दे सकते हैं।
$addressee 2 anim - 11:k1 - respect - -
KAwA_1 3 - - 4:k2 - - - -
banA_1 4 - - 11:rasnegk1 - - - -
awiWi_1 6 - - 12:r6 - - - -
rUpa_1 12 - - 11:k7 - - - -
^OYrdara_1 10 - - 11:k2 - - - -
xe_1-0_sakawA_hE_1 11 - - 0:main - hAz - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_033>
#हालांकि, खाता बनाने से ऑर्डर ट्रैकिंग और भविष्य की आसान खरीदारी जैसे लाभ मिलते हैं।
KAwA_1 2 - - 3:k2 - - - -
banA_1 3 - pl - - - - 19:op1
^OYrdara_1 5 - - - - - - 17:mod
^trEkiMga_1 6 - - 11:r6 - - - 17:head
BaviRya_1 8 - - 11:r6 - - - -
AsAna_1 10 - - 11:mod - - - -
KarIxArI_1 11 - - - - - - 19:op3
lABa_1 13 - - 14:k2 - - - -
mila_1-wA_hE_1 14 - - 0:main - - - -
[6-waw_1] 17 - - - - - - 19:op2
[conj_1] 19 - - 13:re - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_034>
#हां, हम कुछ उत्पादों के लिए थोक या थोक छूट प्रदान करते हैं।
$speaker 2 anim pl 15:k1 - - - -
kuCa_1 3 - - 4:quant - - - -
uwpAxa_1 4 - pl 15:rt - - - -
Woka_1 7 - - - - - - 16:op1
Woka_1 9 - - - - - - 17:mod
CUta_1 10 - - 12:k2 - - - 17:head
[6-waw_1] 17 - - - - - - 16:op2
praxAna_1 11 - - - - - - 15:kriyAmUla
kara_1-wA_hE_1 12 - - - - - - 15:verblizer
[cp_1] 15 - - 0:main - hAz - -
[disjunct_1] 16 - - 15:k2 - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_035a>
#अधिक जानकारी के लिए और अपनी विशिष्ट आवश्यकताओं पर चर्चा करने के लिए कृपया हमारी ग्राहक सहायता टीम से संपर्क करें ।
$addressee 27 anim - 25:k1 - respect - -  
aXika_1 1 - - 2:quant - - - -
jAnakArI_1 2 - - - - - - 26:op1
apanA 6 - - 8:r6 27:coref - - -
viSiRta_1 7 - - 8:mod - - - -
AvaSyakawA_1 8 - pl 25:k7 - - - -
carcA_1 10 - - - - - - 24:kriyAmUla
kara_1 11 - pl - - - - 24:verbalizer
kqpayA_1 14 - - 25:vkvn - - - -
$speaker 15 anim pl 23:r6 - - - -
grAhaka_1 16 - - - - - - 28:mod
sahAyawA_1 17 - - - - - - 28:head
[6-waw_1] 28 - - - - - - 23:mod 
tIma_1 18 - - 21:k4 - - - 23:head
saMparka_1 20 - - - - - - 25:kriyAmUla
kara_1-e_1 21 - - - - - - 25:verbalizer
[4-waw_1] 23 - - 25:k3 - - - -
[cp_1] 24 - - - - - - 26:op2
[cp_2] 25 - - 0:main - - - -
[conj_1] 26 - - 25:rt - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_035b>
#या अधिक जानकारी के लिए और अपनी विशिष्ट आवश्यकताओं पर चर्चा करने के लिए कृपया हमारे थोक पृष्ठ पर जाएँ।
$addressee 23 anim - 19:k1 - respect - -   
aXika_1 1 - - 2:quant - - - -
jAnakArI_1 2 - - - - - - 22:op1
apanA 6 - - 8:r6 23:coref - - -
viSiRta_1 7 - - 8:mod - - - -
AvaSyakawA_1 8 - pl 21:k7 - - - -
carcA_1 10 - - - - - - 21:kriyAmUla
kara_1 11 - pl - - - - 21:verbalizer
kqpayA_1 14 - - 19:vkvn - - - -
$speaker 15 anim pl 17:r6 - - - -
Woka_1 16 - - 17:mod - - - -
pqRTa_1 17 - - 19:k7 - - - -
jA_1-e_1 19 - - 0:main Ecommerce_FAQ_035a.19:anyawra Ecommerce_FAQ_035a.25:samuccaya - -
[cp_1] 21 - - - - - - 22:op2
[conj_1] 22 - - 19:rt - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_036a>
#आपको अपने ऑर्डर में कोई आइटम बदलने या रद्द करने की आवश्यकता है ।
$addressee 1 anim - 13:k4a - respect - -
apanA 2 - pl 3:r6 - - - -
^OYrdara_1 3 - - 7:k7 - - - -
koI 5 - - 6:mod - - - -
Aitama_1 6 - - 7:k2 - - - -
baxala_1 7 - pl - - - - 16:op1
raxxa_1 9 - - - - - - 15:kriyAmUla
kara_1 10 - pl - - - - 15:verbalizer
AvaSyakawA_1 12 - - 13:k1 - - - -
hE_1-pres 13 - - 0:main Ecommerce_FAQ_036b.13:AvaSyakawApariNAma - - -
[cp_1] 15 - - - - - - 16:op2
[disjunct_1] 16 - - 13:r6 - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_036b>
#तो कृपया जितनी जल्दी हो सके हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 5 anim - 15:k1 - respect - -
kqpayA_1 1 - - 15:vkn - - - -
$yax 2 - - 3:quant - - - -
jalxI_1 3 - - 4:k7t - - - -
ho_1 4 - - 12:vmod - - - -
$speaker 6 - pl 9:r6 - - - -
grAhaka_1 7 - - - - - - 14:mod
sahAyawA_1 8 - - - - - - 14:head
^tIma_1 9 - - 12:k5 - - - 16:head
saMparka_1 11 - - 12:pof - - - 15:kriyAmUla
kara_1-o_1 12 - - - - - - 15:verbalizer
[6-waw_1] 14 - - - - - - 16:mod
[4-waw_1] 16 - - 15:k2 - - - -
[cp_1] 15 - - 0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_037>
#हम आवश्यक चरणों में आपकी सहायता करेंगे।
$speaker 1 anim pl 9:k1 - - - -
AvaSyaka_1 2 - - 3:mod - - - -
caraNa_1 3 - pl 9:k7 - - - -
$addressee 5 anim - 6:k2 - respect - -
sahAyawA_1 6 - - 7:pof - - - 9:kriyAmUla
kara_1-gA_1 7 - - - - - - 9:verbalizer
[cp_1] 9 - -  0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_038a>
#उत्पाद समीक्षा देने के लिए, हमारी वेबसाइट पर उत्पाद पृष्ठ पर जाएँ ।
uwpAxa_1 1 - - - - - - 14:mod
samIkRA_1 2 - - - - - - 14:head
xe_1 3 - pl 12:rt - - - -
$speaker 6 anim pl 7:r6 - - - -
^vebasAita_1 7 - - 15:k7p - - - -
uwpAxa_1 9 - - - - - - 15:mod
pqRTa_1 10 - - - - - - 15:head
$addressee 16 anim - 12:k1 respect - - - 
jA_1-e_1 12 - - 0:main - - - -
[6-waw_1] 14 - - 3:k2 - - - -
[6-waw_2] 15 - - 12:k2p - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_038b>
#और 'समीक्षा लिखें' बटन पर क्लिक करें।
$addressee 10 anim -  8:k1 respect - - -
samIkRA_1 1 - - 2:k2 - - - -
liKa_1 2 - pl 3:rvks - - - -
batana_1 3 - - 6:k7p - - - -
^klika_1 5 - - - - - - 8:kriyAmUla
kara_1-o_1 6 - - - Ecommerce_FAQ_038a.12:samuccaya - - 8:verbalizer
[cp_1] 8 - - 0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_039>
#आप उत्पाद के साथ अपने अनुभव के आधार पर अपनी प्रतिक्रिया और रेटिंग साझा कर सकते हैं।
$addressee 1 anim - 15:k1 - respect - -
uwpAxa_1 2 - - 15:rask2 - - - -
apanA 5 - pl 6:r6 - - - -
anuBava_1 6 - - 8:r6 - - - -
AXAra_1 8 - - 15:k7 - - - -
apanA 10 - - 11:r6 - - - -
prawikriyA_1 11 - - - - - - 20:op1
^retiMga_1 13 - - - - - - 20:op2
sAJA_1 14 - - - - - - 19:kriyAmUla
kara_1-0_sakawA_hE_1 15 - - - - - - 19:verbalizer
[cp_1] 19 - - 0:main - - - -
[conj_1] 20 - - 15:k2 - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_040>
#आमतौर पर, प्रत्येक ऑर्डर पर केवल एक प्रोमो कोड लागू किया जा सकता है।
AmawOra+para_1 1 - - 2:mod - - - -
prawyeka_1 3 - - 4:quant - - - -
^OYrdara_1 4 - - 11:k7 - - - -
eka_1 7 - - 18:card - kevala_1 - -
^promo_1 8 - - - - - - 18:mod
^koda_1 9 - - - - - - 18:head
[6-waw_1] 18 - - 17:k2 - - - -
lAgU_1 10 - - - - - - 17:kriyAmUla
kara_1-yA_jA_sakawA_hE_1 11 - - - - - - 17:verbalizer
[cp_1] 17 - -  0:main - - - -
%pass_affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_041>
#चेकआउट प्रक्रिया के दौरान, अपने ऑर्डर पर छूट लागू करने के लिए निर्दिष्ट फ़ील्ड में प्रोमो कोड दर्ज करें।
$addressee 25 anim - 24:k1 - respect - -
^cekaAuta_1 1 - - - - - - 21:mod
prakriyA_1 2 - - 10:k3 - - - 21:head
apanA 5 - pl 6:r6 25:coref - - -
^OYrdara_1 6 - - 23:k7 - - - -
CUta_1 8 - - 23:k2 - - - -
lAgU_1 9 - - - - - - 23:kriyAmUla
kara_1 10 - pl - - - - 23:verbalizer
nirxiRta_1 13 - - 14:mod - - - -
^PZIlda_1 14 - - 19:k7 - - - -
^promo_1 16 - - - - - - 22:mod
^koda_1 17 - - - - - - 22:head
xarja_1 18 - - - - - - 24:kriyAmUla
kara_1-e_1 19 - - - - - - 24:verbalizer
[6-waw_1] 21 - - 24:k7 - - - -
[6-waw_2] 22 - - 24:k2 - - - -
[cp_1] 23 - - 24:rt - - - -
[cp_2] 24 - - 0:main - - - -
%imperative
</sent_id>
<sent_id=Ecommerce_FAQ_042a>
#आपको  अपने ऑर्डर में गलत आइटम मिलता है ।
$addressee 1 anim - 7:k4 - respect - -
apanA 2 - pl 3:r6 1:coref - - -
^OYrdara_1 3 - - 7:k7 - - - -
galawa_1 5 - - 6:mod - - - -
^Aitama_1 6 - - 7:k1 - - - -
mila_1-wA_hE_1 7 - - 0:main Ecommerce_FAQ_042b.12:AvaSyakawApariNAma - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_042b>
#तो कृपया तुरंत हमारी ग्राहक सहायता टीम से संपर्क करें।
kqpayA_1 1 - - 9:vkvn - - - -
$addressee 13 anim - 7:k4 - respect - -
wuraMwa_1 2 - - 9:krvn - - - -
$speaker 3 anim pl 6:r6 - - - -
grAhaka_1 4 - - - - - - 11:mod
sahAyawA_1 5 - - - - - - 11:head
^tIma_1 6 - - 9:rask1 - - - -
saMparka_1 8 - - - - - - 12:kriyAmUla
kara_1-0_1 9 - - - - - - 12:verbalizer
[6-waw_1] 11 - - - - - - 14:mod
[4-waw_1] 14 - - - - - - 14:head
[cp_1] 12 - - 0:main - - - -
%affirmative
</sent_id>
<sent_id=Ecommerce_FAQ_043a>
#हम आपके लिए सही आइटम भेजने की व्यवस्था करेंगे ।
$speaker 1 - pl 11:k1 - - - -
$addressee 2 -  - 6:k4 - respect  - -
sahI_1 4 - - 5:mod - - - -
^Aitama_1 5 - - 11:k2 - - - -
Beja_1 6 - pl 11:rt - - - -
vyavasWA_1 8 - - - - - - 11:kriyAmUla
kara_1-gA_1 9 - - - - - - 11:verbalizer
[cp_1] 11 - - 0:main - - - -
%affirmative
</sent_id>


<sent_id=Ecommerce_FAQ_043b>
 #और हम गलत आइटम को वापस करने में सहायता करेंगे।
 $speaker 1 anim pl 12:k1 - - - -
 galawa_1 2 - - 3:mod - - - -
 Aitama_1 3 - - 11:k2 - - - -
 vApasa_1 5 - - - - - - 11:kriyAmUla
 kara_1 6 - pl - - - - 11:verbalizer
 sahAyawA_1 8 - - - - - - 12:kriyAmUla
 kara_1-gA_1 9 - - - - - - 12:verbalizer
 [cp_1] 11 - - 12:k7 - - - -
 [cp_2] 12 - - 0:main - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_044>
 #हाँ, हम तेज़ डिलीवरी के लिए शीघ्र शिपिंग विकल्प प्रदान करते हैं।
  $speaker 2 anim pl 15:k1 - - - -
 wejZa_1 3 - - 4:mod - - - -
 ^dilIvarI_1 4 - - 15:rt - - - -
 SIGra_1 7 - - 15:krvn - - - -
 ^SipiMga_1 8 - - - - - - 14:mod
 vikalpa_1 9 - - - - - - 14:head
 praxAna_1 10 - - - - - - 15:kriyAmUla
 kara_1-wA_hE_1 11 - - - - - - 15:verbalizer
 [6-waw_1] 14 - - 15:k2 - - - -
 [cp_1] 15 - - 0:main - hAz - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_045>
 #चेकआउट प्रक्रिया के दौरान, आप इच्छित शीघ्र शिपिंग विधि का चयन कर सकते हैं।
 ^cekaAuta_1 1 - - - - - - 16:mod
 prakriyA_1 2 - - 12:ras-neg - - - 16:head
 $addressee 5 anim - 12:k1 - respect - -
 icCiwa_1 6 - - 12:krvn - - - -
 SIGra_1 7 - - 12:krvn - - - -
 ^SipiMga 8 - - 9:pof__cn - - - 16:mod
 viXi 9 female - 11:k2 - - - 16:head
 cayana_1 11 - - 12:pof - - - 18:kriyAmUla
 kara_1-0_sakawA_hE_1 12 - - 0:main - - - 18:verbalizer
 [6-waw_1] 16 - - rur - - - -
 [cp_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_046a>
 #कोई उत्पाद वर्तमान में स्टॉक में नहीं है ।
 koI_1 1 - - 2:quant - - - -
 uwpAxa_1 2 - - 8:k1 - - - -
 varwamAna_1 3 - - 8:k7t - - - -
 ^stOYka_1 5 - - 8:k7p - - - -
 nahIM_1 7 - - 8:neg - - - -
 hE_1-pres 8 - - 0:main Ecommerce_FAQ_046b.13:AvaSyakawApariNAma - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_046b>
 #तो आपको आमतौर पर उत्पाद सूचनाओं के लिए साइन अप करने का विकल्प दिखाई देगा।
 $addressee 1 anim - 13:k1 - respect - -
 AmawOra+para_1 2 - - 13:vkvn - - - -
 uwpAxa_1 4 - - - - - - 16:mod
 sUcanA_1 5 - pl 13:rt - - - 16:head
 ^sAina+^apa_1 8 - - - - - - 18:kriyAmUla
 kara_1 10 - pl 12:r6 - - - 18:verbalizer
 vikalpa_1 12 - - 13:k2 - - - -
 xiKa_1-AI_xegA_1 13 - - 0:main - - - -
 [6-waw_1] 16 - - - - - - -
 [cp_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_047a>
 #इस तरह, जब उत्पाद फिर से उपलब्ध होगा ।
 $wyax 1 - - 2:dem - proximal - -
 waraha_1 2 - - 8:k7t - - - -
 uwpAxa_1 4 - - 8:k1 - - - -
 Pira_1 5 - - 8:krvn - sA_1 - -
 upalabXa_1 7 - - 8:pof - - - -
 ho_1-gA_1 8 - - 0:main Ecommerce_FAQ_047b.6:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_047b>
 #तो आपको सूचित किया जाएगा।
 $addressee 1 anim - 3:k2 - respect - -
 sUciwa_1 2 - - 3:pof - - - 6:kriyAmUla
 kara_1-yA_jA_gA_1 3 - - 0:main - - - 6:verbalizer
 [cp_1] 6 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_048>
 #हमारा ईमेल के द्वारा भेजा गया न्यूज़लेटर नए उत्पाद रिलीज़, विशेष ऑफ़र और हमारे उत्पादों से संबंधित उपयोगी सुझावों पर अपडेट प्रदान करता है।
 $speaker 1 anim pl 3:r6 - - - -
 ^Imela_1 2 - - 3:pof__cn - - - -
Beja_1 25 - - - - - - -
 ^nyUjZaletara_1 3 - - 0:k1 - - - -
 nae_1 4 - - 5:mod - - - -
 uwpAxa_1 5 - - 19:mod - - - -
 rilIjZa_1 6 - - 0:fragof - - - -
 viSeRa_1 7 - - 8:mod - - - -
 ^OYPZara_1 8 - - 13:intf - - - -
 $speaker 10 anim pl 11:r6 - - - -
 uwpAxa_1 11 - pl 13:intf - - - -
 saMbaMXiwa_1 13 - - 15:mod - - - -
 upayogI_1 14 - - 15:mod - - - -
 suJAva_1 15 - pl 19:k7 - - - -
 ^apadeta_1 17 - - 19:k2 - - - -
 praxAna_1 18 - - 19:pof - - - -
 kara_1-wA_hE_1 19 - - 0:main - - - -
 [nc_1] 22 - - - - - - -
 [cp_1] 23 - - - - - - -
 [conj_1] 24 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_049>
 #आप हमारी वेबसाइट पर हमारे न्यूज़लेटर की सदस्यता ले सकते हैं।
 $addressee 1 anim - 9:k1 - respect - -
 $speaker 2 anim pl 3:r6 - - - -
 ^vebasAita_1 3 - - 9:k7 - - - -
 $speaker 5 anim pl 6:r6 - - - -
 ^nyUjZaletara_1 6 - - 8:k2 - - - -
 saxasyawA_1 8 - - 9:k2 - - - -
 le_1-0_sakawA_hE_1 9 - - 0:main - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_050a>
 #हाँ, आप अपना विचार बदलते हैं ।
 hAz_1 1 - - 0:mod - - - -
 $addressee 2 anim - 5:k1 - respect - -
 apanA 3 - pl 4:r6 2:coref - - -
 vicAra_1 4 - - 5:k2 - - - -
 baxala_1-wA_hE_1 5 - - 0:main Ecommerce_FAQ_050b.5:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_050b>
 #तो आप उत्पाद वापस कर सकते हैं।
 $addressee 1 anim - 4:k1 - respect - -
 uwpAxa_1 2 - - 4:k2 - - - -
 vApasa_1 3 - - 4:pof - - - 8:kriyAmUla
 kara_1-0_saka_hE_1 4 - - 0:main - - - 8:verbalizer
 [cp_1] 8 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_051a>
 #कृपया आप यह सुनिश्चित करें ।
 kqpayA_1 1 - - 5:k1 - - - -
 $addressee 2 anim - 5:k1 - respect - -
 $wyax 3 - - 5:k2 Ecommerce_FAQ_051b.8:coref proximal - -
 suniSciwa_1 4 - - 5:pof - - - 7:kriyAmUla
 kara_1-o_1 5 - - 0:main - - - 7:verbalizer
 [cp_1] 7 - - - - - - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_051b>
 #कि उत्पाद अपनी मूल स्थिति और पैकेजिंग में है ।
 uwpAxa_1 1 - - 8:k1 - - - -
 apanA 2 - - 4:r6 1:coref - - -
 mUla_1 3 - - 4:mod - - - 11:mod
 sWiwi_1 4 - - 8:k1s - - - 11:head
 ^pEkejiMga_1 6 - - 8:k1s - - - 10:op2
 hE_1-pres 8 - - 0:main - - - -
 [conj_1] 10 - - - - - - -
[nc_1] 11 - - - - - - 10:op1
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_051c>
 #और निर्देशों के लिए हमारी वापसी नीति देखें ।
 nirxeSa_1 1 - pl 7:rt - - - -
$addressee 8 anim - - - respect - - 
$speaker 4 anim pl 6:r6 - - - -
 vApasI_1 5 - - 6:pof__cn - - - 9:mod
 nIwi_1 6 - - 7:k2 - - - 9:head
 xeKa_1-o_1 7 - - 0:main Ecommerce_FAQ_051a.7:samuccaya - - -
 [nc_1] 9 - - - - - - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_052>
 #हाँ, हम अपने व्यावसायिक घंटों के दौरान अपनी वेबसाइट पर लाइव चैट सहायता प्रदान करते हैं।
 hAz_1 1 - - 0:k1 - - - -
 $speaker 2 anim pl 15:k1 - - - -
 apanA 3 - pl 5:r6 2:coref - - -
 vyAvasAyika_1 4 - - 5:mod - - - -
 GaMtA_1 5 - pl 15:k7t - - - -
 apanA 8 - - 9:r6 - - - -
 ^vebasAita_1 9 - - 15:k7 - - - -
 ^lAiva_1 11 - - 13:pof__cn - - - 18:mod
 ^cEta_1 12 - - 13:pof__cn - - - 18:head
 sahAyawA_1 13 - - 15:k2 - - - -
 praxAna_1 14 - - 15:pof - - - 19:kriyAmUla
 kara_1-wA_hE_1 15 - - 0:main - - - 19:verbalizer
 [nc_1] 18 - - - - - - -
 [cp_1] 19 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_053>
 #हमारी ग्राहक सहायता टीम के साथ चैट शुरू करने के लिए नीचे दाएँ कोने में चैट आइकन देखें।
$addressee 23 - - - - respect  - -
 $speaker 1 - pl 4:r6 - - - -
 grAhaka_1 2 - - 4:pof__cn - - - 20:mod
 sahAyawA_1 3 - - 4:pof__cn - - - 20:head
 ^tIma_1 4 - - 9:ras-k1 - - - 21:head
 cEta_1 7 - - 9:k2 - - - -
 SurU_1 8 - - 9:pof - - - 22:kriyAmUla
 kara_1 9 - pl 18:rt - - - 22:verbalizer
 nIcA_1 12 - pl 18:k7p - - - -
 xAyAz 13 - - 14:mod - - - -
 konA_1 14 - pl 18:k7p - - - -
 ^cEta_1 16 - - 17:pof__cn - - - 23:mod
 ^Aikana_1 17 - - 18:k2 - - - 23:head
 xeKa_1-o_1 18 - - 0:main - - - -
 [nc_1] 20 - - - - - - 21:mod
 [nc_2] 21 - - - - - - -
 [cp_1] 22 - - - - - - -
[nc_3] 23 - - - - - - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_054a>
 #हाँ, आप उपहार के रूप में उत्पाद ऑर्डर कर सकते हैं ।
 hAz_1 1 - - 0:mod - - - -
 $addressee 2 - - 9:k1 - respect  - -
 upahAra_1 3 - - 9:k7 - - - -
 uwpAxa_1 7 - - 8:pof__cn - - - -
 ^OYrdara_1 8 - - 9:pof - - - 14:kriyAmUla
 kara_1-0_saka_hE_1 9 - - 0:main - - - 14:verblizer
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_054b>
 #और इसे सीधे प्राप्तकर्ता को भेज सकते हैं।
 $wyax 1 - - 5:k2 Ecommerce_FAQ_054a.7:coref proximal - -
 sIXA_1 2 - pl 5:krvn - - - -
 prApwakarwA_1 3 - - 5:k4 - - - -
 Beja_1-0_sakawA_hE_1 5 - - 0:main Ecommerce_FAQ_054a.14:samuccaya - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_055>
 #चेकआउट प्रक्रिया के दौरान, आप प्राप्तकर्ता का शिपिंग पता दर्ज कर सकते हैं।
 cekaAuta_1 1 - - 2:pof__cn - - - 15:mod
 prakriyA_1 2 - - 11:k3 - - - 15:head
 $addressee 5 - - 11:k1 - respect  - -
 prApwakarwA_1 6 - - 9:r6 - - - -
 ^SipiMga_1 8 - - 9:pof__cn - - - 16:mod
 pawA_1 9 - - 11:k2 - - - 16:head
 xarja_1 10 - - 11:pof - - - 17:kriyAmUla
 kara_1-0_saka_hE_1 11 - - 0:main - - - 17:verblizer
 [nc_1] 15 - - - - - - -
 [nc_2] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_056a>
 #आपका डिस्काउंट कोड काम नहीं कर रहा है ।
 $addressee 1 - - 3:r6 -respect - - -
 diskAuMta_1 2 - - 3:pof__cn - - - 10:mod
 koda_1 3 - - 6:k2 - - - 10:head
 kAma_1 4 - - 6:pof - - - 11:kriyAmUla
 nahIM_1 5 - - 6:neg - - - 11:verblizer
 kara_1-0_rahA_hE_1 6 - - 0:main Ecommerce_FAQ_056b.13:AvaSyakawApariNAma - - -
 [nc_1] 10 - - - - - - -
 [cp_1] 11 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_056b>
 #तो कृपया कोड से जुड़े नियमों और शर्तों को दोबारा जाँच लें।
$addressee 16 - - - - respect  - -
 kqpayA 1 - - 11:k1 - - - -
 koda_1 2 - - 4:k2 - - - -
 judZa_1 4 - - 5:rvks - - - -
 niyama_1 5 - pl 11:k2 - - - 15:op1
 Sarwa_1 7 - pl 11:k2 - - - 15:op2
 xobArA_1 9 - - 11:krvn - - - -
 jAzca_1 10 - - 11:pof - - - 13:kriyAmUla
 le_1-o_1 11 - - 0:main - - - 13:verblizer
 [cp_1] 13 - - - - - - -
 [conj_1] 15 - - - - - - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_057a>
 #समस्या बनी रहती है ।
 samasyA_1 1 - - 2:k1 - - - -
 bana_1-yA_rahawA_hE_1 2 - - 0:main Ecommerce_FAQ_057b.13 :AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_057b>
 #तो सहायता के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 16 - - - - respect  - -
 sahAyawA_1 1 - - 10:rt - - - -
 $speaker 4 - pl 7:r6 - - - -
 grAhaka_1 5 - - 7:pof__cn - - - 12:mod
 sahAyawA_1 6 - - 7:pof__cn - - - 12:head
 ^tIma_1 7 - - 10:k2 - - - 14:head
 saMparka_1 9 - - 10:pof - - - 13:kriyAmUla
 kara_1-o_1 10 - - 0:main - - - 13:verblizer
 [nc_1] 12 - - - - - - 14:mod
 [nc_2] 14 - - - - - - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_058>
 #अंतिम सेल आइटम आमतौर पर वापसी योग्य और धनवापसी योग्य नहीं होते हैं।
 aMwima_1 1 - - 3:mod - - - -
 ^sela_1 2 - - 3:pof__cn - - - 15:mod
 ^Aitama_1 3 - - 12:k1 - - - 15:head
 AmawOra_1 4 - - 12:k7 - - - -
 vApasI_1 6 - - 7:intf - - - 17:mod
 yogya_1 7 - - 12:rt - - - 17:head
 XanavApasI_1 9 - - 12:rt - - - 18:mod
 yogya_1 10 - - 12:k1s - - - 18:head
 nahIM_1 11 - - 12:neg - - - -
 ho_1-wA_hE_1 12 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
[nc_2] 17 - - - - - - 16:op1
[nc_3] 18 - - - - - - 16:op2
 [conj_1] 16 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_059a>
 #कृपया उत्पाद विवरण की समीक्षा करें ।
$addressee 10 - - - - respect  - -
 kqpayA 1 - - 3:pof__cn - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - 8:mod
 vivaraNa_1 3 - - 5:k2 - - - 8:head
 samIkRA_1 5 - - 6:pof - - - 9:kriyAmUla
 kareM_1-wA_hE_1 6 - - 0:main - - - 9:verblizer
 [nc_1] 8 - - - - - - -
 [cp_1] 9 - - - - - - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_059b>
 #या विशिष्ट आइटम के लिए वापसी पात्रता की पुष्टि करने के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 24 - - - - respect  - -
 viSiRta_1 1 - - 2:mod - - - 25:mod
 ^Aitama_1 2 - - 9:rt - - - 25:head
[nc_1] 25 - - - - - - -
 vApasI_1 5 - - 6:pof__cn - - - 26:mod
 pAwrawA_1 6 - - 8:k2 - - - 26:head
[nc_2] 26 - - - - - - -
 puRti_1 8 - - 9:pof - - - 22:kriyAmUla
 kara_1 9 - pl 18:rt - - - 22:verblizer
 $speaker 12 - pl 15:r6 - - - -
 grAhaka_1 13 - - 15:pof__cn - - - 20:mod
 sahAyawA_1 14 - - 15:pof__cn - - - 20:head
 ^tIma_1 15 - - 18:k2 - - - 21:head
 saMparka_1 17 - - 18:pof - - - 23:kriyAmUla
 kara_1-o_1 18 - - 0:main Ecommerce_FAQ_059a.18:anyawra - - 23:verblizer
 [nc_3] 20 - - - - - - 21:mod
 [nc_4] 21 - - - - - - -
 [cp_1] 22 - - - - - - -
 [cp_2] 23 - - - - - - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_060>
 #चुनिंदा उत्पादों के लिए इंस्टॉलेशन सेवाएँ उपलब्ध हैं।
 cuniMxA_1 1 - - 2:mod - - - -
 uwpAxa_1 2 - pl 8:rt - - - -
 ^iMstOYleSana_1 5 - - 6:pof__cn - - - 10:mod
 sevA_1 6 - pl 8:k1 - - - 10:head
 upalabXa_1 7 - - 8:k1s - - - -
 hE_1-pres 8 - - 0:main - - - -
 [nc_1] 10 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_061a>
 #कृपया उत्पाद विवरण देखें या अधिक जानकारी के लिए और इंस्टॉलेशन सेवाओं का अनुरोध करने के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 5 - - - - respect  - -
 kqpayA 1 - - 3:pof__cn - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - 27:mod
 vivaraNa_1 3 - - 4:k2 - - - 27:head
 xeKa_1 4 - pl 5:ccof - - - -
 [nc_1] 27 - - - - - - -
 %imperative
 </sent_id>

<sent_id=Ecommerce_FAQ_061b>
 #या अधिक जानकारी के लिए और इंस्टॉलेशन सेवाओं का अनुरोध करने के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 5 - - - - respect  - -
 aXika_1 6 - - 7:quant - - - -
 jAnakArI_1 7 - - 14:rt - - - 31:op1
 ^iMstOYleSana_1 11 - - 12:pof__cn - - - 26:mod
 sevA_1 12 - pl 14:k2 - - - 26:head
 anuroXa_1 14 - - 15:pof - - - 29:kriyAmUla
 kara_1 15 - pl 24:rt - - - 29:verbalizer 
 $speaker 18 - pl 21:r6 - - - -
 grAhaka_1 19 - - 21:pof__cn - - - 27:mod
 sahAyawA_1 20 - - 21:pof__cn - - - 27:head
 ^tIma_1 21 - - 24:k2 - - - 28:head
 saMparka_1 23 - - 24:pof - - - 30:kriyAmUla
 kara_1-o_1 24 - - 5:ccof - - - 30:verbalizer
 [nc_1] 26 - - - - - - -
[nc_2] 27 - - - - - - 28:mod
 [nc_3] 28 - - - - - - -
 [cp_1] 29 - - - - - - 31:op2
 [cp_2] 30 - - - - - - -
 [conj_1] 31 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_062>
 #बंद हो चुके उत्पाद अब खरीद के लिए उपलब्ध नहीं हैं।
 baMxa_1 1 - - 2:pof - - - -
 ho_1 2 - - 4:rvks - [shade:cuka_1] - -
 uwpAxa_1 4 - - 11:k1 - - - -
 aba 5 - - 11:k7t - - - -
 KarIxa_1 6 - - 11:rt - - - -
 upalabXa_1 9 - - 11:k1s - - - -
 nahIM_1 10 - - 11:neg - - - -
 hE_1-pres 11 - - 0:main - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_063>
 #हम अपनी वेबसाइट पर वैकल्पिक उत्पादों की खोज करने की सलाह देते हैं।
 $speaker 1 - pl 12:k1 - - - -
 apanA 2 - - 3:r6 - - - -
 ^vebasAita_1 3 - - 9:k7 - - - -
 vEkalpika_1 5 - - 6:mod - - - -
 uwpAxa_1 6 - pl 8:k2 - - - -
 Koja_1 8 - - 9:pof - - - 15:kriyAmUla
 kara_1 9 - pl 11:k2 - - - -15:verbalizer
 salAha_1 11 - - 12:pof - - - 16:kriyAmUla
 xe_1-wA_hE_1 12 - - 0:main - - - 16:verbalizer
 [cp_1] 15 - - - - - - -
 [cp_2] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_064>
 #आम तौर पर रिटर्न के लिए रसीद या खरीद का प्रमाण आवश्यक होता है।
 Ama+wOra_1 1 - - 2:mod - - - -
 ^ritarna_1 4 - - 13:rt - - - -
 rasIxa_1 7 - - 11:r6 - - - 17:op1
 KarIxa_1 9 - - 11:r6 - - - 17:op2
 pramANa_1 11 - - 13:k1 - - - -
 AvaSyaka_1 12 - - 13:pof - - - -
 ho_1-wA_hE_1 13 - - 0:main - - - -
 [disjunct_1] 17 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_065a>
 #कृपया हमारी वापसी नीति देखें ।
$addressee 6 - - - - respect  - -
 kqpayA 1 - - 5:k1 - - - -
 $speaker 2 - pl 4:r6 - - - -
 vApasI_1 3 - - 4:pof__cn - - - 18:mod
 nIwi_1 4 - - 5:k2 - - - 18:head
 xeKa_1-o_1 5 - - 0:main - - - -
[nc_1] 18 - - - - - - -
%imperative
 </sent_id>

<sent_id=Ecommerce_FAQ_065b>
 #या सहायता के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
$addressee 1 - - - - respect  - -
 sahAyawA_1 7 - - 16:rt - - - -
 $speaker 10 - pl 13:r6 - - - -
 grAhaka_1 11 - - 13:pof__cn - - - 18:mod
 sahAyawA_1 12 - - 13:pof__cn - - - 18:head
 ^tIma_1 13 - - 16:k2 - - - 19:head
 saMparka_1 15 - - 16:pof - - - 20:kriyAmUla
 kara_1-o_1 16 - - 0:main - - - 20:verbalizer
 [nc_1] 18 - - - - - - 19:mod
 [nc_2] 19 - - - - - - -
 [cp_1] 20 - - - - Ecommerce_FAQ_065a.18:samuccaya - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_066>
 #हाँ, हम चुनिंदा देशों में अंतर्राष्ट्रीय शिपिंग प्रदान करते हैं।
  $speaker 2 - pl 9:k1 - - - -
 cuniMxA_1 3 - - 4:mod - - - -
 xeSa_1 4 - pl 9:k7p - - - -
 aMwarrARtrIya_1 6 - - 7:mod - - - -
 ^SipiMga_1 7 - - 9:k2 - - - -
 praxAna_1 8 - - 9:pof - - - 12:kriyAmUla
 kara_1-wA_hE_1 9 - - 0:main - - - 12:verbalizer
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_067a>
 #कृपया चेकआउट के दौरान उपलब्ध शिपिंग गंतव्यों की समीक्षा करें।
$addressee 1 - - - - respect  - -
 kqpayA 11 - - 10:k1 - - - -
 ^cekaAuta_1 2 - - 5:intf - - - -
 upalabXa_1 5 - - 7:mod - - - 12:mod
 SipiMga_1 6 - - 7:pof__cn - - - 12:head
[nc_1] 12 - - - - - - 13:mod
 gaMwavya_1 7 - - 9:k2 - - - 13:head
[nc_2] 13 - - - - - - -
 samIkRA_1 9 - - 10:pof - - - 14:kriyAmUla
 kareM_1-wA_hE_1 10 - - 0:main - - - 14:verbalizer
[cp_1] 14 - - - - - - -
%imperative
 </sent_id>

<sent_id=Ecommerce_FAQ_067b>
 #या सहायता के लिए हमारे ग्राहक सहायता से संपर्क करें।
$addressee 11 - - - - respect  - -
 sahAyawA_1 12 - - 20:rt - - - -
 $speaker 15 - pl 17:r6 - - - -
 grAhaka_1 16 - - 17:pof__cn - - - 22:mod
 sahAyawA_1 17 - - 20:k2 - - - 22:head
 saMparka_1 19 - - 20:pof - - - 24:kriyAmUla
 kara_1-o_1 20 - - 0:main - - - 24:verbalizer
 [nc_1] 22 - - - - - - -
 [cp_1] 24 - - - - Ecommerce_FAQ_067a.14:samuccaya - -
 %imperative
 </sent_id>
<sent_id=Ecommerce_FAQ_068>
 #हाँ, आप चेकआउट प्रक्रिया के दौरान उपहार संदेश जोड़ सकते हैं।
 $addressee 2 - - 9:k1 - - - -
 ^cekaAuta_1 3 - - 4:pof__cn - - - 13:mod
 prakriyA_1 4 - - 9:k7t - - - 13:head 
 xOrAna_1 6 - - 4:k7p - - - -
 upahAra_1 7 - - 8:pof__cn - - - 14:mod
 saMxeSa_1 8 - - 9:k2 - - - 14:head
 jodZa_1-0_sakawA_hE_1 9 - - 0:main - hAz - -
 [6-waw_1] 13 - - - - - - -
 [4-waw_2] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_069>
 #आम तौर पर यह एक अनुभाग होता है जहाँ आप अपना व्यक्तिगत संदेश दर्ज कर सकते हैं।
 Ama+wOra+para_1 1 - - 2:mod - - - -
 $wyax 4 - - 7:k1 - proximal - -
 eka_2 5 - - 6:card - - - -
 anuBAga_1 6 - - 7:k1s - - - -
 ho_1-wA_hE_1 7 - - 0:main - - - -
 $yax 9 - - 15:k7p 6:coref - - -
 $addressee 10 - - 15:k1 - respect  - -
 apanA 11 - pl 13:r6 10:coref - - -
 vyakwigawa_1 12 - - 13:mod - - - 20:mod
 saMxeSa_1 13 - - 15:k2 - - - 20:head
 xarja_1 14 - - 15:pof - - - 19:kriyAmUla
 kara_1-0_sakawA_hE_1 15 - pl 7:rc - - - 19:verbalizer
 [cp_1] 19 - - - - - - -
[karmaXAraya_1] 20 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_070>
 #हम वर्तमान में खरीदारी से पहले उत्पाद प्रदर्शन की पेशकश नहीं करते हैं।
 $speaker 1 - pl 12:k1 - - - -
 varwamAna_1 2 - - 12:k7 - - - -
 KarIxArI_1 4 - - 12:k7t - - - -
 pahalA_1 6 - pl 4:k7p - - - -
 uwpAxa_1 7 - - 8:pof__cn - - - -
 praxarSana_1 8 - - 10:k2 - - - -
 peSakaSa_1 10 - - 12:pof - - - -
 nahIM_1 11 - - 12:neg - - - -
 kara_1-wA_hE_1 12 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [cp_1] 16 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_071>
 #हालाँकि, आप हमारी वेबसाइट पर विस्तृत उत्पाद विवरण, विनिर्देश और ग्राहक समीक्षाएँ पा सकते हैं।
 $addressee 2 - - 13:k1 - respect  - -
 $speaker 3 - pl 4:r6 - - - -
 vebasAita_1 4 - - 13:k7 - - - -
 viswqwa_1 6 - - 7:mod - - - -
 uwpAxa_1 7 - - 13:k1 - - - -
 vivaraNa, 8 - - 9:pof__cn - - - -
 vinirxeSa_1 9 - - 13:k1 - - - -
 grAhaka_1 11 - - 13:k1 - - - -
 samIkRA_1 12 - pl 13:k2 - - - -
 pA_1-0_saka_hE_1 13 - - 0:main - - - -
 [nc_1] 17 - - - - - - -
 [conj_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_072>
 #'जल्द ही आने वाला' के रूप में सूचीबद्ध उत्पाद तत्काल खरीद के लिए उपलब्ध नहीं हैं।
 jalxa_1 1 - - 3:krvn - - - -
 A_1 3 - pl 16:k7 - - - -
 sUcIbaxXa_1 8 - - 9:mod - - - -
 uwpAxa_1 9 - - 16:k1 - - - -
 wawkAla_1 10 - - 16:krvn - - - -
 KarIxa_1 11 - - 16:rt - - - -
 upalabXa_1 14 - - 16:k1s - - - -
 nahIM_1 15 - - 16:neg - - - -
 hE_1-pres 16 - - 0:main - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_073>
 #कृपया उत्पाद उपलब्ध होने पर सूचित करने के लिए अधिसूचनाओं के लिए साइन अप करें।
 kqpayA 1 - - 15:k1 - - - -
 uwpAxa_1 2 - - 4:k2 - - - -
 upalabXa_1 3 - - 4:pof - - - -
 ho_1 4 - pl 7:rblsk - - - -
 sUciwa_1 6 - - 7:pof - - - -
 kara_1 7 - pl 15:rt - - - -
 aXisUcanA_1 10 - pl 15:rt - - - -
 sAina_1 13 - - 15:pof - - - -
 apa_1 14 - - 15:pof - - - -
 kareM_1-wA_hE_1 15 - - 0:main - - - -
 [cp_1] 17 - - - - - - -
 [cp_2] 18 - - - - - - -
 [cp_3] 19 - - - - - - -
 [cp_4] 20 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_074>
 #हाँ, आमतौर पर आपके ऑर्डर के साथ इनवॉइस शामिल होता है।
 hAz, 1 - - 0:k1 - - - -
 AmawOra_1 2 - - 10:k7 - - - -
 $addressee 4 - - 5:r6 - respect  - -
 OYrdara_1 5 - - 10:ras-k1 - - - -
 sAWa_1 7 - - 5:k7p - - - -
 inavOYisa_1 8 - - 10:k1 - - - -
 SAmila_1 9 - - 10:pof - - - -
 ho_1-wA_hE_1 10 - - 0:main - - - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_075a>
 #आपको अलग से इनवॉइस की आवश्यकता है ।
 $addressee 1 - - 7:k4a - - - -
 alaga_1 2 - - 7:krvn - - - -
 inavOYisa_1 4 - - 6:r6 - - - -
 AvaSyakawA_1 6 - - 7:k1 - - - -
 hE_1-pres 7 - - 0:main Ecommerce_FAQ_075b.7:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_075b>
 #तो कृपया अपने ऑर्डर विवरण के साथ हमारी ग्राहक सहायता टीम से संपर्क करें।
 kqpayA 1 - - 13:k1 - - - -
 apanA 2 - pl 4:r6 - - - -
 OYrdara_1 3 - - 4:pof__cn - - - -
 vivaraNa_1 4 - - 13:ras-k1 - - - -
 sAWa_1 6 - - 4:k7p - - - -
 $speaker 7 - pl 10:r6 - - - -
 grAhaka_1 8 - - 10:pof__cn - - - -
 sahAyawA_1 9 - - 10:pof__cn - - - -
 ^tIma_1 10 - - 13:k4 - - - -
 saMparka_1 12 - - 13:pof - - - -
 kareM_1-wA_hE_1 13 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [nc_2] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_076>
 #'सीमित संस्करण' उत्पादों की उपलब्धता सीमित हो सकती है।
 sImiwa_1 1 - - 3:mod - - - -
 saMskaraNa_1 2 - - 3:pof__cn - - - -
 uwpAxa_1 3 - pl 5:r6 - - - -
 upalabXawA_1 5 - - 7:k1 - - - -
 sImiwa_1 6 - - 7:pof - - - -
 ho_1-0_saka_ho_1 7 - - 0:main - - - -
 [nc_1] 11 - - - - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_077>
 #हम आपके आइटम को सुरक्षित करने के लिए जल्द से जल्द ऑर्डर देने की सलाह देते हैं।
 $speaker 1 - pl 16:k1 - - - -
 $addressee 2 - - 3:r6 - - - -
 Aitama_1 3 - - 6:k2 - - - -
 surakRiwa_1 5 - - 6:pof - - - -
 kara_1 6 - pl 13:rt - - - -
 jalxa_1 9 - - 13:krvn - - - -
 jalxa_1 11 - - 13:krvn - - - -
 OYrdara_1 12 - - 13:k2 - - - -
 xe_1 13 - pl 15:k2 - - - -
 salAha_1 15 - - 16:pof - - - -
 xe_1-wA_hE_1 16 - - 0:main - - - -
 [cp_1] 19 - - - - - - -
 [cp_2] 20 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_078a>
 #जबकि किसी उत्पाद को उसकी मूल पैकेजिंग में वापस करना बेहतर होता है ।
 kisI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 9:k2 - - - -
 $wyax 4 - - 6:r6 - distal - -
 mUla_1 5 - - 6:mod - - - -
 pEkejiMga_1 6 - - 9:k7 - - - -
 vApasa_1 8 - - 9:pof - - - -
 kara_1 9 - - 11:k1 - - - -
 behawara_1 10 - - 11:pof - - - -
 ho_1-wA_hE_1 11 - - 0:main Ecommerce_FAQ_077.11:viroXI_xyowaka - - -
 [cp_1] 14 - - - - - - -
 [cp_2] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_078b>
 #आप उसके बिना भी वापसी शुरू कर सकते हैं।
 $addressee 1 - - 7:k1 - - - -
 $wyax 2 - - 7:k2 - distal - -
 vApasI_1 5 - - 7:k2 - - - -
 SurU_1 6 - - 7:pof - - - -
 kara_1-0_saka_hE_1 7 - - 0:main - - - -
 [cp_1] 11 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_079>
 #ऐसे मामलों में मार्गदर्शन के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
 EsA 1 - pl 2:dem - - - -
 mAmalA_1 2 - pl 13:k7 - - - -
 mArgaxarSana_1 4 - - 13:rt - - - -
 $speaker 7 - pl 10:r6 - - - -
 grAhaka_1 8 - - 10:pof__cn - - - -
 sahAyawA_1 9 - - 10:pof__cn - - - -
 ^tIma_1 10 - - 13:k2 - - - -
 saMparka_1 12 - - 13:pof - - - -
 kareM_1-wA_hE_1 13 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [cp_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_080>
 #हम स्टॉक में नहीं आने वाले उत्पादों के लिए आरक्षण प्रदान नहीं करते हैं।
 $speaker 1 - pl 13:k1 - - - -
 stOYka_1 2 - - 5:k7 - - - -
 nahIM_1 4 - - 5:neg - - - -
 A_1 5 - pl 7:mod - - - -
 uwpAxa_1 7 - pl 13:rt - - - -
 ArakRaNa_1 10 - - 13:k2 - - - -
 praxAna_1 11 - - 13:pof - - - -
 nahIM_1 12 - - 13:neg - - - -
 kara_1-wA_hE_1 13 - - 0:main - - - -
 [cp_1] 16 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_081a>
 #हालाँकि, आप उत्पाद सूचनाओं के लिए साइन अप कर सकते हैं ।
 $addressee 2 - - 9:k1 - - - -
 uwpAxa_1 3 - - 4:pof__cn - - - -
 sUcanA_1 4 - pl 9:rt - - - -
 sAina_1 7 - - 9:k2 - - - -
 apa_1 8 - - 9:pof - - - -
 kara_1-0_saka_hE_1 9 - - 0:main - - - -
 [nc_1] 13 - - - - - - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_081b>
 #ताकि जब यह फिर से उपलब्ध हो जाए।
 $yax 1 - - 6:k7t - - - -
 $wyax 2 - - 6:k1 - proximal - -
 Pira_1 3 - - 6:krvn - - - -
 upalabXa_1 5 - - 6:pof - - - -
 ho_1-e_1 6 - - 0:main - [shade:jA_1] - -
 $addressee 9 - - 11:k2 - - - -
 sUciwa_1 10 - - 11:pof - - - -
 kara_1-yA_jA_subj_saka_1 11 - - 0:main - - - -
 [cp_1] 15 - - - - - - -
 [cp_2] 16 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_081c>
#तो आपको सूचित किया जा सके।
$addressee 9 - - 11:k2 - - - -
 sUciwa_1 10 - - 11:pof - - - 15:kriyAmUla
 kara_1-yA_jA_saka_1 11 - - 0:main - - - verbalizer
 [cp_1] 15 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_082>
 #हाँ, आप प्री-ऑर्डर और इन-स्टॉक आइटम के मिश्रण के साथ ऑर्डर दे सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 12:k1 - - - -
 prI-OYrdara 3 - - 8:r6 - - - -
 ina-stOYka 5 - - 6:pof__cn - - - -
 Aitama_1 6 - - 8:r6 - - - -
 miSraNa_1 8 - - 12:ras-k2 - - - -
 sAWa_1 10 - - 8:k7p - - - -
 OYrdara_1 11 - - 12:k2 - - - -
 xe_1-subj_saka_hE_1 12 - - 0:main - - - -
 [nc_1] 16 - - - - - - -
 [conj_1] 17 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_083a>
 #हालाँकि, कृपया ध्यान दें कि सभी आइटम उपलब्ध होने के बाद पूरा ऑर्डर भेजा जाएगा।
$addressee 1 - - 4:k1 - - - -
 kqpayA 2 - - 4:k1 - - - -
$wyax 5 - - 4:k2 - - - -
 XyAna_1 3 - - 4:pof - - - -
 xe_1-o_1 4 - - 0:main - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_083b>
 #कि सभी आइटम उपलब्ध होने के बाद पूरा ऑर्डर भेजा जाएगा।
saBI_1 6 - - 7:quant - - - -
 ^Aitama_1 7 - - 9:k1 - - - -
 upalabXa_1 8 - - 9:pof - - - -
 ho_1 9 - pl 4:vk2 - - - -
 bAxa_1 11 - - 9:k7p - - - -
 pUrA_1 12 - - 13:mod - - - -
 ^OYrdara_1 13 - - 14:k2 - - - -
 Beja_1 14 - - 4:k2 - - - -
 [cp_1] 17 - - - - - - -
 [cp_2] 18 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_084a>
 #आपका उत्पाद शिपिंग के दौरान क्षतिग्रस्त हो गया था ।
 $addressee 1 - - 3:r6 - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 ^SipiMga_1 3 - - 7:k7t - - - -
 xOrAna_1 5 - - 3:k7p - - - -
 kRawigraswa_1 6 - - 7:pof - - - -
 ho_1-yA1_WA_1 7 - - 0:main Ecommerce_FAQ_084b.7:AvaSyakawApariNAma [shade:jA_1] - -
 [nc_1] 11 - - - - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_084b>
 #तो कृपया तुरंत हमारी ग्राहक सहायता टीम से संपर्क करें।
 kqpayA 1 - - 9:k1 - - - -
 wuraMwa_1 2 - - 9:krvn - - - -
 $speaker 3 - pl 6:r6 - - - -
 grAhaka_1 4 - - 6:pof__cn - - - -
 sahAyawA_1 5 - - 6:pof__cn - - - -
 ^tIma_1 6 - - 9:ras-k1 - - - -
 saMparka_1 8 - - 9:pof - - - -
 kareM_1-wA_hE_1 9 - - 0:main - - - -
 [nc_1] 11 - - - - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_085>
 #हम आपको वापसी और रिप्लेस्मेंट प्रक्रिया के माध्यम से मार्गदर्शन करेंगे।
 $speaker 1 - pl 11:k1 - - - -
 $addressee 2 - - 11:k4 - - - -
 vApasI_1 3 - - 11:k7 - - - -
 ^riplesmeMta_1 5 - - 6:pof__cn - - - -
 prakriyA_1 6 - - 11:k7 - - - -
 mArgaxarSana_1 10 - - 11:pof - - - -
 kara_1-gA_1 11 - - 0:main - - - -
 [nc_1] 13 - - - - - - -
 [cp_1] 14 - - - - - - -
 [conj_1] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_086>
 #हम जब भी संभव हो लोकप्रिय उत्पादों को फिर से स्टॉक करने का प्रयास करते हैं।
 $speaker 1 - pl 15:k1 - - - -
 $yax 2 - - 5:k7t - - - -
 saMBava_1 4 - - 5:pof - - - -
 ho_1 5 - - 15:vmod - - - -
 lokapriya_1 6 - - 7:mod - - - -
 uwpAxa_1 7 - pl 12:k2 - - - -
 Pira_1 9 - - 12:krvn - - - -
 stOYka_1 11 - - 12:pof - - - -
 kara_1 12 - pl 14:k2 - - - -
 prayAsa_1 14 - - 15:pof - - - -
 kara_1-wA_hE_1 15 - - 0:main - - - -
 [cp_1] 18 - - - - - - -
 [cp_2] 19 - - - - - - -
 [cp_3] 20 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_087a>
 #कृपया उत्पाद सूचनाओं के लिए साइन अप करें ।
$addressee 12 - - 11:k1 - - - -
 kqpayA 1 - - 8:k1 - - - 10:mod
 uwpAxa_1 2 - - 3:pof__cn - - - 10:head
 sUcanA_1 3 - pl 8:rt - - - -
 ^sAina+^apa_1 6 - - 8:pof - - - 11:kriyAmUla
 kara_1-o_1 8 - - 0:main - - - 11:verbalizer
 [6-waw_1] 10 - - - - - - -
 [cp_1] 11 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_087b>
 #ताकि जब आइटम फिर से उपलब्ध हो जाए तो आपको सूचित किया जा सके।
 $yax 1 - - 6:k7t - - - -
 ^Aitama_1 2 - - 6:k1 - - - -
 Pira_1 3 - - 6:krvn - - - -
 upalabXa_1 5 - - 6:pof - - - -
 ho_1-e_2 6 - - 8:vmod - [shade:jA_1] - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_087c>
 #तो आपको सूचित किया जा सके।
 $addressee 9 - - 11:k2 - - - -
 sUciwa_1 10 - - 11:pof - - - 15:kriyAmUla
 kara_1-yA_jA_subj_saka_1 11 - - 0:main - - - 15:verbalizer
 [cp_1] 15 - - - - - - -
 %pass_affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_088a>
 #'बैकऑर्डर' के रूप में सूचीबद्ध उत्पाद अस्थायी रूप से स्टॉक से बाहर हैं ।
 bEkaOYrdara 1 - - 13:k7 - - - -
 sUcIbaxXa_1 5 - - 6:mod - - - -
 uwpAxa_1 6 - - 13:k1 - - - -
 asWAyI_1 7 - - 8:mod - - - -
 rUpa_1 8 - - 13:krvn - - - -
 stOYka_1 10 - - 13:k7 - - - -
 bAhara_1 12 - - 10:k7p - - - -
 hE_1-pres 13 - - 0:main - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_088b>
 #लेकिन फिर भी ऑर्डर किए जा सकते हैं।
 Pira_1 1 - - 4:krvn - - - -
 OYrdara_1 3 - - 4:pof - - - -
 kara_1-yA_jA_1 4 - - 0:main Ecommerce_FAQ_088a.4:viroXI - - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_089>
 #उत्पाद के फिर से स्टॉक होने पर आपका ऑर्डर पूरा हो जाएगा।
 uwpAxa_1 1 - - 6:k1 - - - -
 Pira_1 3 - - 6:krvn - - - -
 stOYka_1 5 - - 6:k1 - - - -
 ho_1 6 - pl 11:rblsk - - - -
 $addressee 8 - - 9:r6 - - - -
 OYrdara_1 9 - - 11:k1 - - - -
 pUrA_1 10 - - 11:pof - - - -
 ho_1-gA_1 11 - - 0:main - [shade:jA_1] - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_090>
 #हाँ, आप सेल के दौरान या छूट के साथ खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:k1 - - - -
 $addressee 2 - - 15:k7t - - - -
 xOrAna_1 5 - - 2:k7p - - - -
 CUta_1 7 - - 10:k2 - - - -
 sAWa_1 9 - - 7:k7p - - - -
 KarIxa_1 10 - - 12:rbks - - - -
 uwpAxa_1 12 - - 15:k2 - - - -
 vApasa_1 14 - - 15:pof - - - -
 kara_1-0_saka_hE_1 15 - - 0:main - - - -
 [cp_1] 19 - - - - - - -
 [disjunct_1] 20 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_091>
 #छूट के बाद भुगतान की गई राशि के आधार पर रिफ़ंड प्रोसेस किया जाएगा।
 CUta_1 1 - - 5:k7t - - - -
 bAxa_1 3 - - 1:k7p - - - -
 BugawAna_1 4 - - 5:pof - - - -
 kara_1 5 - - 7:rbks - - - -
 rASi_1 7 - - 9:r6 - - - -
 AXAra_1 9 - - 13:k7 - - - -
 riPZMda_1 11 - - 12:pof__cn - - - -
 prosesa_1 12 - - 13:pof - - - -
 kara_1-yA_jA_gA_1 13 - - 0:main - - - -
 [nc_1] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 [cp_2] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_092a>
 #आपको कोई क्षतिग्रस्त उत्पाद प्राप्त होता है ।
 $addressee 1 - - 6:k1 - - - -
 koI 2 - - 4:mod - - - -
 kRawigraswa_1 3 - - 4:mod - - - -
 uwpAxa_1 4 - - 6:k1 - - - -
 prApwa_1 5 - - 6:pof - - - -
 ho_1-wA_hE_1 6 - - 0:main Ecommerce_FAQ_092b.6:AvaSyakawApariNAma - - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_092b>
 #तो कृपया हमारी ग्राहक सहायता टीम से तुरंत संपर्क करें।
 kqpayA 1 - - 9:k1 - - - -
 $speaker 2 - pl 5:r6 - - - -
 grAhaka_1 3 - - 5:pof__cn - - - -
 sahAyawA_1 4 - - 5:pof__cn - - - -
 ^tIma_1 5 - - 9:k2 - - - -
 wuraMwa_1 7 - - 9:krvn - - - -
 saMparka_1 8 - - 9:pof - - - -
 kareM_1-wA_hE_1 9 - - 0:main - - - -
 [nc_1] 11 - - - - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_093>
 #हम मरम्मत या रिप्लेस्मेंट के लिए आवश्यक चरणों में आपकी सहायता करेंगे।
 $speaker 1 - pl 12:k1 - - - -
 marammawa_1 2 - - 12:k7 - - - -
 riplesmeMta_1 4 - - 12:k7 - - - -
 AvaSyaka_1 7 - - 8:mod - - - -
 caraNa_1 8 - pl 12:k7 - - - -
 $addressee 10 - - 11:k2 - - - -
 sahAyawA_1 11 - - 12:pof - - - -
 kara_1-gA_1 12 - - 0:main - - - -
 [cp_1] 14 - - - - - - -
 [disjunct_1] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_094a>
 #कोई उत्पाद प्री-ऑर्डर के लिए उपलब्ध है ।
 koI 1 - - 3:mod - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 prI-OYrdara 3 - - 7:rt - - - -
 upalabXa_1 6 - - 7:k1s - - - -
 hE_1-pres 7 - - 0:main Ecommerce_FAQ_094b.7:AvaSyakawApariNAma - - -
 [nc_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_094b>
 #तो आप अपना आइटम सुरक्षित करने के लिए ऑर्डर दे सकते हैं।
 $addressee 1 - - 9:k1 - - - -
 apanA 2 - pl 3:r6 - - - -
 Aitama_1 3 - - 5:k2 - - - -
 surakRiwa_1 4 - - 5:pof - - - -
 kara_1 5 - pl 9:rt - - - -
 OYrdara_1 8 - - 9:k2 - - - -
 xe_1-subj_saka_hE_1 9 - - 0:main - - - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_095>
 #उत्पाद उपलब्ध होने पर उसे भेज दिया जाएगा।
 uwpAxa_1 1 - - 3:k1 - - - -
 upalabXa_1 2 - - 3:pof - - - -
 ho_1 3 - pl 6:rblsk - - - -
 $wyax 5 - - 6:k2 - distal - -
 Beja_1-yA_jA_1 6 - - 0:main - [shade:xe_1] - -
 [cp_1] 10 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_096>
 #हाँ, आप उपहार के रूप में खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 12:k1 - - - -
 upahAra_1 3 - - 7:k7 - - - -
 KarIxa_1 7 - - 9:rbks - - - -
 uwpAxa_1 9 - - 12:k2 - - - -
 vApasa_1 11 - - 12:pof - - - -
 kara_1-0_saka_hE_1 12 - - 0:main - - - -
 [cp_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_097>
 #हालाँकि, आम तौर पर खरीद के लिए उपयोग की गई मूल भुगतान विधि से धनवापसी जारी की जाएगी।
 Ama_1 2 - - 3:mod - - - -
 wOra_1 3 - - 9:k7 - - - -
 KarIxa_1 5 - - 9:rt - - - -
 upayoga_1 8 - - 9:pof - - - -
 kara_1 9 - - 13:rbks - - - -
 mUla_1 11 - - 13:mod - - - -
 BugawAna_1 12 - - 13:pof__cn - - - -
 viXi 13 female - 17:k5 - - - -
 XanavApasI_1 15 - - 17:k2 - - - -
 jArI_1 16 - - 17:pof - - - -
 kara_1-yA_jA_gA_1 17 - - 0:main - - - -
 [nc_1] 20 - - - - - - -
 [cp_1] 21 - - - - - - -
 [cp_2] 22 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_098a>
 #दुर्भाग्य से किसी उत्पाद को 'बंद' के रूप में सूचीबद्ध किया गया है ।
 xurBAgya_1 1 - - 11:krvn - - - -
 kisI 3 - - 4:mod - - - -
 uwpAxa_1 4 - - 11:k2 - - - -
 baMxa_1 6 - - 11:k7 - - - -
 sUcIbaxXa_1 10 - - 11:pof - - - -
 kara_1-yA_jA_yA_hE_1 11 - - 0:main Ecommerce_FAQ_098b.11:AvaSyakawApariNAma - - -
 [cp_1] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_098b>
 #तो वह अब खरीद के लिए उपलब्ध नहीं है।
 $wyax 1 - - 8:k1 - distal - -
 aba 2 - - 8:k7t - - - -
 KarIxa_1 3 - - 8:rt - - - -
 upalabXa_1 6 - - 8:k1s - - - -
 nahIM_1 7 - - 8:neg - - - -
 hE_1-pres 8 - - 0:main - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_099>
 #हम अपनी वेबसाइट पर वैकल्पिक उत्पादों की खोज करने की सलाह देते हैं।
 $speaker 1 - pl 12:k1 - - - -
 apanA 2 - - 3:r6 - - - -
 vebasAita_1 3 - - 9:k7 - - - -
 vEkalpika_1 5 - - 6:mod - - - -
 uwpAxa_1 6 - pl 8:k2 - - - -
 Koja_1 8 - - 9:pof - - - -
 kara_1 9 - pl 11:k2 - - - -
 salAha_1 11 - - 12:pof - - - -
 xe_1-wA_hE_1 12 - - 0:main - - - -
 [cp_1] 15 - - - - - - -
 [cp_2] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_100a>
 #कोई उत्पाद 'बिक चुका है' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 3:k1 - - - -
 bika_1 3 - - 10:k7 - - - -
 sUcIbaxXa_1 9 - - 10:k1s - - - -
 hE_1-pres 10 - - 0:main Ecommerce_FAQ_100b.10:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_100b>
 #तो वह वर्तमान में खरीद के लिए उपलब्ध नहीं है।
 $wyax 1 - - 9:k1 - distal - -
 varwamAna_1 2 - - 9:k7 - - - -
 KarIxa_1 4 - - 9:rt - - - -
 upalabXa_1 7 - - 9:k1s - - - -
 nahIM_1 8 - - 9:neg - - - -
 hE_1-pres 9 - - 0:main - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_101a>
 #कृपया बाद में फिर से जाँच करें ।
 kqpayA 1 - - 7:k1 - - - -
 bAxa_1 2 - - 7:k7t - - - -
 Pira_1 4 - - 7:krvn - - - -
 jAzca_1 6 - - 7:pof - - - -
 kareM_1-wA_hE_1 7 - - 0:main - - - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_101b>
 #या उपलब्ध होने पर सूचना प्राप्त करने के लिए साइन अप करें।
 upalabXa_1 1 - - 2:pof - - - -
 ho_1 2 - pl 6:rblsk - - - -
 sUcanA_1 4 - - 6:k2 - - - -
 prApwa_1 5 - - 6:pof - - - -
 kara_1 6 - pl 11:rt - - - -
 sAina_1 9 - - 11:k2 - - - -
 apa_1 10 - - 11:pof - - - -
 kareM_1-wA_hE_1 11 - - 0:main Ecommerce_FAQ_101a.11:anyawra - - -
 [cp_1] 13 - - - - - - -
 [cp_2] 14 - - - - - - -
 [cp_3] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_102>
 #हाँ, आप उपहार कार्ड से खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 11:k1 - - - -
 upahAra_1 3 - - 4:pof__cn - - - -
 kArda_1 4 - - 6:k5 - - - -
 KarIxa_1 6 - - 8:rbks - - - -
 uwpAxa_1 8 - - 11:k2 - - - -
 vApasa_1 10 - - 11:pof - - - -
 kara_1-0_saka_hE_1 11 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [cp_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_103>
 #रिफ़ंड स्टोर क्रेडिट या नए उपहार कार्ड के रूप में जारी किया जाएगा।
 riPZMda_1 1 - - 3:pof__cn - - - -
 stora_1 2 - - 3:pof__cn - - - -
 kredita_1 3 - - 12:k2 - - - -
 nae_1 5 - - 7:mod - - - -
 upahAra_1 6 - - 7:pof__cn - - - -
 kArda_1 7 - - 12:k2 - - - -
 jArI_1 11 - - 12:pof - - - -
 kara_1-yA_jA_gA_1 12 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [nc_2] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 [disjunct_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_104a>
 #कोई उत्पाद आपके साइज में उपलब्ध नहीं है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 8:k1 - - - -
 $addressee 3 - - 4:r6 - - - -
 sAija_1 4 - - 8:k7 - - - -
 upalabXa_1 6 - - 8:k1s - - - -
 nahIM_1 7 - - 8:neg - - - -
 hE_1-pres 8 - - 0:main Ecommerce_FAQ_104b.8:AvaSyakawApariNAma - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_104b>
 #तो यह अस्थायी रूप से स्टॉक से बाहर हो सकता है।
 $wyax 1 - - 8:k1 - proximal - -
 asWAyI_1 2 - - 3:mod - - - -
 rUpa_1 3 - - 8:krvn - - - -
 stOYka_1 5 - - 8:k5 - - - -
 bAhara_1 7 - - 8:pof - - - -
 ho_1-0_saka_ho_1 8 - - 0:main - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_105a>
 #कृपया बाद में फिर से जाँच करें।
$addressee 8 anim - 7:k1 - - - -
 kqpayA 1 - - 0:k1 - - - -
 bAxa_1 2 - - 7:k7t - - - -
 Pira_1 4 - - 7:krvn - - - -
 jAzca_1 6 - - 7:pof - - - 8:kriyAmUla
 kara_1-o_1 7 - - 0:main - - - 8:verbalizer
 [cp_1] 8 - - - - - - -
 %imperative
 </sent_id>

<sent_id=Ecommerce_FAQ_105b>
 #या साइज सूचना के लिए साइन अप करें।
$addressee 8 anim - 7:k1 - - - -
 sAija_1 9 - - 10:pof__cn - - - -
 sUcanA_1 10 - - 15:rt - - - -
 ^sAina+^apa_1 13 - - 15:pof - - - 18:kriyAmUla
 kara_1-o_1 15 - - 0:main - - - 18:verbalizer
 [6-waw_1] 17 - - - - - - -
 [cp_1] 18 - - - - - - -
 %imperative 
 </sent_id>

<sent_id=Ecommerce_FAQ_106a>
 #कोई उत्पाद 'जल्द ही आने वाला' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 5:k1 - - - -
 jalxa_1 3 - - 5:krvn - - - -
 A_1 5 - pl 11:k7 - - - -
 sUcIbaxXa_1 10 - - 11:k1s - - - -
 hE_1-pres 11 - - 0:main Ecommerce_FAQ_106c.11:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_106b>
 #और वह प्री-ऑर्डर के लिए उपलब्ध है ।
 $wyax 1 - - 6:k1 - distal - -
 prI-OYrdara 2 - - 6:rt - - - -
 upalabXa_1 5 - - 6:k1s - - - -
 hE_1-pres 6 - - 0:main Ecommerce_FAQ_106a.6:samuccaya - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_106c>
 #तो आप उपलब्ध होने से पहले अपने आइटम को सुरक्षित करने के लिए ऑर्डर दे सकते हैं।
 $addressee 1 - - 3:k1 - - - -
 upalabXa_1 2 - - 3:pof - - - -
 ho_1 3 - pl 14:rblak - - - -
 pahalA_1 5 - pl 3:k7p - - - -
 apanA 6 - pl 7:r6 - - - -
 Aitama_1 7 - - 10:k2 - - - -
 surakRiwa_1 9 - - 10:pof - - - -
 kara_1 10 - pl 14:rt - - - -
 OYrdara_1 13 - - 14:k2 - - - -
 xe_1-subj_saka_hE_1 14 - - 0:main - - - -
 [cp_1] 18 - - - - - - -
 [cp_2] 19 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_107>
 #हाँ, आप छूट कोड के साथ खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 12:k1 - - - -
 CUta_1 3 - - 4:pof__cn - - - -
 koda_1 4 - - 7:ras-k1 - - - -
 sAWa_1 6 - - 4:k7p - - - -
 KarIxa_1 7 - - 9:rbks - - - -
 uwpAxa_1 9 - - 12:k2 - - - -
 vApasa_1 11 - - 12:pof - - - -
 kara_1-0_saka_hE_1 12 - - 0:main - - - -
 [nc_1] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_108>
 #छूट के बाद भुगतान की गई राशि के आधार पर रिफ़ंड प्रोसेस किया जाएगा।
 CUta_1 1 - - 5:k7t - - - -
 bAxa_1 3 - - 1:k7p - - - -
 BugawAna_1 4 - - 5:pof - - - -
 kara_1 5 - - 7:rbks - - - -
 rASi_1 7 - - 9:r6 - - - -
 AXAra_1 9 - - 13:k7 - - - -
 riPZMda_1 11 - - 12:pof__cn - - - -
 prosesa_1 12 - - 13:pof - - - -
 kara_1-yA_jA_gA_1 13 - - 0:main - - - -
 [nc_1] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 [cp_2] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_109>
 #हम वर्तमान में कस्टम ऑर्डर या वैयक्तिकृत उत्पाद प्रदान नहीं करते हैं।
 $speaker 1 - pl 11:k1 - - - -
 varwamAna_1 2 - - 11:k7 - - - -
 kastama_1 4 - - 5:pof__cn - - - -
 OYrdara_1 5 - - 11:k2 - - - -
 vEyakwikqwa_1 7 - - 8:mod - - - -
 uwpAxa_1 8 - - 11:k2 - - - -
 praxAna_1 9 - - 11:pof - - - -
 nahIM_1 10 - - 11:neg - - - -
 kara_1-wA_hE_1 11 - - 0:main - - - -
 [nc_1] 14 - - - - - - -
 [cp_1] 15 - - - - - - -
 [disjunct_1] 16 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_110>
 #कृपया हमारी वेबसाइट पर उपलब्ध उत्पादों का पता लगाएँ।
 kqpayA 1 - - 9:k1 - - - -
 $speaker 2 - pl 3:r6 - - - -
 vebasAita_1 3 - - 5:intf - - - -
 upalabXa_1 5 - - 6:mod - - - -
 uwpAxa_1 6 - pl 8:k2 - - - -
 pawA_1 8 - - 9:pof - - - -
 lagA_1-e_1 9 - - 0:main - - - -
 [cp_1] 11 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_111a>
 #कोई उत्पाद 'अस्थायी रूप से अनुपलब्ध' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 11:k1 - - - -
 asWAyI_1 3 - - 4:mod - - - -
 rUpa_1 4 - - 11:krvn - - - -
 anupalabXa_1 6 - - 11:k7 - - - -
 sUcIbaxXa_1 10 - - 11:k1s - - - -
 hE_1-pres 11 - - 0:main Ecommerce_FAQ_111c.11:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_111b>
 #तो वह स्टॉक से बाहर है ।
 $wyax 1 - - 5:k1 - distal - -
 stOYka_1 2 - - 5:k7 - - - -
 bAhara_1 4 - - 2:k7p - - - -
 hE_1-pres 5 - - 0:main - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_111c>
 #लेकिन भविष्य में उसे फिर से स्टॉक किया जा सकता है।
 BaviRya_1 1 - - 7:k7 - - - -
 $wyax 3 - - 7:k2 - distal - -
 Pira_1 4 - - 7:krvn - - - -
 stOYka_1 6 - - 7:pof - - - -
 kara_1-yA_jA_1 7 - - 0:main Ecommerce_FAQ_111b.7:viroXI - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_112a>
 #कृपया बाद में फिर से जाँचें।
 kqpayA 1 - - 0:k1 - - - -
 bAxa_1 2 - - 6:k7t - - - -
 Pira_1 4 - - 6:krvn - - - -
 jAzca_1-e_1 6 - - 0:main - - - -
 sUcanA_1 8 - pl 13:rt - - - -
 sAina_1 11 - - 13:pof - - - -
 apa_1 12 - - 13:pof - - - -
 kareM_1-wA_hE_1 13 - - 0:main - - - -
 [cp_1] 15 - - - - - - -
 [cp_2] 16 - - - - - - -
 [disjunct_1] 17 - - - - - - -
 %affirmative
 </sent_id>

 <sent_id=Ecommerce_FAQ_112b>
 #या सूचनाओं के लिए साइन अप करें।
 kqpayA 1 - - 0:k1 - - - -
 bAxa_1 2 - - 6:k7t - - - -
 Pira_1 4 - - 6:krvn - - - -
 jAzca_1-e_1 6 - - 0:main - - - -
 sUcanA_1 8 - pl 13:rt - - - -
 sAina_1 11 - - 13:pof - - - -
 apa_1 12 - - 13:pof - - - -
 kareM_1-wA_hE_1 13 - - 0:main - - - -
 [cp_1] 15 - - - - - - -
 [cp_2] 16 - - - - - - -
 [disjunct_1] 17 - - - - - - -
 %affirmative
 </sent_id>

<sent_id=Ecommerce_FAQ_113>
 #हमारी वापसी नीति आम तौर पर उन उत्पादों को कवर करती है जो आगमन पर दोषपूर्ण या क्षतिग्रस्त हैं।
 $speaker 1 - pl 3:r6 - - - -
 vApasI_1 2 - - 3:pof__cn - - - -
 nIwi_1 3 - - 11:k1 - - - -
 Ama_1 4 - - 5:mod - - - -
 wOra_1 5 - - 11:k7 - - - -
 $wyax 7 - pl 8:dem - distal - -
 uwpAxa_1 8 - pl 11:k4 - - - -
 kavara_1 10 - - 11:pof - - - -
 kara_1-wA_hE_1 11 - - 0:main - - - -
 $yax 13 - - 19:k1 - - - -
 Agamana_1 14 - - 19:k7 - - - -
 xoRapUrNa_1 16 - - 19:k1s - - - -
 kRawigraswa_1 18 - - 19:k1s - - - -
 hE_1 19 - pl 11:rc - - - -
 [nc_1] 21 - - - - - - -
 [cp_1] 22 - - - - - - -
 [disjunct_1] 23 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_114>
 #अनुचित उपयोग के कारण हुई क्षति, वापसी के लिए योग्य नहीं हो सकती है।
 anuciwa_1 1 - - 2:mod - - - -
 upayoga_1 2 - - 5:rh - - - -
 ho_1 5 - - 12:vmod - - - -
 vApasI_1 7 - - 12:rt - - - -
 yogya_1 10 - - 12:k1s - - - -
 nahIM_1 11 - - 12:neg - - - -
 ho_1-yA_saka_ho_1 12 - - 0:main - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_115>
 #सहायता के लिए कृपया हमारी ग्राहक सहायता टीम से संपर्क करें।
 sahAyawA_1 1 - - 11:rt - - - -
 kqpayA 4 - - 11:k1 - - - -
 $speaker 5 - pl 8:r6 - - - -
 grAhaka_1 6 - - 8:pof__cn - - - -
 sahAyawA_1 7 - - 8:pof__cn - - - -
 tIma_1 8 - - 11:k4 - - - -
 saMparka_1 10 - - 11:pof - - - -
 kareM_1-wA_hE_1 11 - - 0:main - - - -
 [nc_1] 13 - - - - - - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_116a>
 #कोई उत्पाद 'जल्द ही आ रहा है' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 5:k1 - - - -
 jalxa_1 3 - - 5:krvn - - - -
 A_1 5 - - 12:k7 - - - -
 sUcIbaxXa_1 11 - - 12:k1s - - - -
 hE_1-pres 12 - - 0:main Ecommerce_FAQ_116e.12:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_116b>
 #लेकिन वह प्री-ऑर्डर के लिए उपलब्ध नहीं है ।
 $wyax 1 - - 7:k1 - distal - -
 prI-OYrdara 2 - - 7:rt - - - -
 upalabXa_1 5 - - 7:k1s - - - -
 nahIM_1 6 - - 7:neg - - - -
 hE_1-pres 7 - - 0:main Ecommerce_FAQ_116a.7:viroXI - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_116c>
 #तो आपको तब तक प्रतीक्षा करनी होगी ।
 $addressee 1 - - 5:k1 - - - -
 waba 2 - - 5:k7t - - - -
 prawIkRA_1 4 - - 5:pof - - - -
 kara_1-nA_ho_1 5 - - 0:main - - - -
 [cp_1] 8 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_116d>
 #जब तक कि वह आधिकारिक रूप से रिलीज़ न हो जाए ।
 $wyax 3 - - 9:k1 - distal - -
 AXikArika_1 4 - - 5:mod - - - -
 rUpa_1 5 - - 9:krvn - - - -
 rilIjZa_1 7 - - 9:pof - - - -
 na_1 8 - - 9:neg - - - -
 ho_1-e_1 9 - - 0:main - [shade:jA_1] - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_116e>
 #और जब तक कि वह खरीद के लिए उपलब्ध न हो जाए।
 $yax 1 - - 10:k7t - - - -
 $wyax 4 - - 10:k1 - distal - -
 KarIxa_1 5 - - 10:rt - - - -
 upalabXa_1 8 - - 10:pof - - - -
 na_1 9 - - 10:neg - - - -
 ho_1-e_1 10 - - 0:main Ecommerce_FAQ_116d.10:samuccaya [shade:jA_1] - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_117a>
 #कोई उत्पाद 'होल्ड पर' के रूप में सूचीबद्ध है ।
 koI 1 - - 3:mod - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 holda 3 - - 9:k7 - - - -
 sUcIbaxXa_1 8 - - 9:k1s - - - -
 hE_1-pres 9 - - 0:main Ecommerce_FAQ_117b.9:AvaSyakawApariNAma - - -
 [nc_1] 11 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_117b>
 #तो वह अस्थायी रूप से खरीद के लिए अनुपलब्ध है।
 $wyax 1 - - 9:k1 - distal - -
 asWAyI_1 2 - - 3:mod - - - -
 rUpa_1 3 - - 9:krvn - - - -
 KarIxa_1 5 - - 9:rt - - - -
 anupalabXa_1 8 - - 9:k1s - - - -
 hE_1-pres 9 - - 0:main - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_118a>
 #कृपया बाद में जाँच करें ।
 kqpayA 1 - - 5:k1 - - - -
 bAxa_1 2 - - 5:k7t - - - -
 jAzca_1 4 - - 5:pof - - - -
 kareM_1-wA_hE_1 5 - - 0:main - - - -
 [cp_1] 7 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_118b>
 #या उपलब्ध होने पर सूचना प्राप्त करने के लिए साइन अप करें।
 upalabXa_1 1 - - 2:pof - - - -
 ho_1 2 - pl 6:rblsk - - - -
 sUcanA_1 4 - - 6:k2 - - - -
 prApwa_1 5 - - 6:pof - - - -
 kara_1 6 - pl 11:rt - - - -
 sAina_1 9 - - 11:k2 - - - -
 apa_1 10 - - 11:pof - - - -
 kareM_1-wA_hE_1 11 - - 0:main Ecommerce_FAQ_118a.11:anyawra - - -
 [cp_1] 13 - - - - - - -
 [cp_2] 14 - - - - - - -
 [cp_3] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_119a>
 #जबकि वापसी के लिए रसीद को प्राथमिकता दी जाती है ।
 vApasI_1 1 - - 7:rt - - - -
 rasIxa_1 4 - - 7:k4 - - - -
 prAWamikawA_1 6 - - 7:pof - - - -
 xe_1-yA_jA_wA_hE_1 7 - - 0:main Ecommerce_FAQ_118b.7:viroXI_xyowaka - - -
 [cp_1] 11 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_119b>
 #हम इसके बिना भी आपकी सहायता कर सकते हैं।
 $speaker 1 - pl 7:k1 - - - -
 $wyax 2 - - 7:vmod - proximal - -
 $addressee 5 - - 6:k2 - - - -
 sahAyawA_1 6 - - 7:pof - - - -
 kara_1-0_saka_hE_1 7 - - 0:main - - - -
 [cp_1] 11 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_120>
 #कृपया आगे के मार्गदर्शन के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
 kqpayA 1 - - 13:k1 - - - -
 AgA_1 2 - pl 4:r6 - - - -
 mArgaxarSana_1 4 - - 13:rt - - - -
 $speaker 7 - pl 10:r6 - - - -
 grAhaka_1 8 - - 10:pof__cn - - - -
 sahAyawA_1 9 - - 10:pof__cn - - - -
 ^tIma_1 10 - - 13:k2 - - - -
 saMparka_1 12 - - 13:pof - - - -
 kareM_1-wA_hE_1 13 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [cp_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_121>
 #एक बार सीमित संस्करण का उत्पाद बिक जाने के बाद, उसे फिर से स्टॉक नहीं किया जा सकता है।
 eka_1 1 - - 2:card - - - -
 bAra_1 2 - - 7:k7t - - - -
 sImiwa_1 3 - - 4:mod - - - -
 saMskaraNa_1 4 - - 6:r6 - - - -
 uwpAxa_1 6 - - 7:k1 - - - -
 bika_1 7 - - 16:vmod - [shade:jA_1] - -
 $wyax 11 - - 16:k2 - distal - -
 Pira_1 12 - - 16:krvn - - - -
 stOYka_1 14 - - 16:pof - - - -
 nahIM_1 15 - - 16:neg - - - -
 kara_1-yA_jA_nA_saka_1 16 - - 0:main - - - -
 [cp_1] 21 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_122a>
 #सीमित संस्करण के आइटम सीमित समय के लिए ही उपलब्ध होते हैं ।
 sImiwa_1 1 - - 2:mod - - - -
 saMskaraNa_1 2 - - 4:r6 - - - -
 Aitama_1 4 - - 11:k1 - - - -
 sImiwa_1 5 - - 6:mod - - - -
 samaya_1 6 - - 11:rt - - - -
 upalabXa_1 10 - - 11:pof - - - -
 ho_1-wA_hE_1 11 - - 0:main - - - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_122b>
 #इसलिए हम उन्हें उपलब्ध होने पर खरीद लेने की सलाह देते हैं।
 $speaker 1 - pl 10:k1 - - - -
 $wyax 2 - pl 4:k2 - distal - -
 upalabXa_1 3 - - 4:pof - - - -
 ho_1 4 - pl 10:rblsk - - - -
 KarIxa_1 6 - - 7:pof - - - -
 le_1 7 - pl 9:k2 - - - -
 salAha_1 9 - - 10:pof - - - -
 xe_1-wA_hE_1 10 - - 0:main Ecommerce_FAQ_122a.10:pariNAma - - -
 [cp_1] 13 - - - - - - -
 [cp_2] 14 - - - - - - -
 [cp_3] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_123a>
 #कोई उत्पाद 'बंद' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 8:k1 - - - -
 baMxa_1 3 - - 8:k7 - - - -
 sUcIbaxXa_1 7 - - 8:k1s - - - -
 hE_1-pres 8 - - 0:main Ecommerce_FAQ_123c.8:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_123b>
 #लेकिन फिर भी वह वेबसाइट पर दिखाई दे रहा है ।
 Pira_1 1 - - 6:krvn - - - -
 $wyax 3 - - 6:k1 - distal - -
 vebasAita_1 4 - - 6:k7 - - - -
 xiKA_1-subj_raha_1 6 - - 0:main Ecommerce_FAQ_123a.6:viroXI - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_123c>
 #तो यह एक त्रुटि हो सकती है।
 $wyax 1 - - 4:k1 - proximal - -
 eka_1 2 - - 3:card - - - -
 wruti_1 3 - - 4:k1s - - - -
 ho_1-0_saka_ho_1 4 - - 0:main - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_124>
 #कृपया स्पष्टीकरण के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
 kqpayA 1 - - 11:k1 - - - -
 spaRtIkaraNa_1 2 - - 11:rt - - - -
 $speaker 5 - pl 8:r6 - - - -
 grAhaka_1 6 - - 8:pof__cn - - - -
 sahAyawA_1 7 - - 8:pof__cn - - - -
 ^tIma_1 8 - - 11:k2 - - - -
 saMparka_1 10 - - 11:pof - - - -
 kareM_1-wA_hE_1 11 - - 0:main - - - -
 [nc_1] 13 - - - - - - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_125>
 #निकासी या अंतिम सेल आइटम आमतौर पर गैर-वापसी योग्य और गैर-वापसी योग्य होते हैं।
 nikAsI_1 1 - - 8:k2 - - - -
 aMwima_1 3 - - 5:mod - - - -
 sela_1 4 - - 5:pof__cn - - - -
 Aitama_1 5 - - 8:k2 - - - -
 AmawOra_1 6 - - 8:k7 - - - -
 gEra-vApasI 8 - - 13:k1 - - - -
 yogya_1 9 - - 10:ccof - - - -
 gEra-vApasI 11 - - 10:ccof - - - -
 yogya_1 12 - - 13:pof - - - -
 ho_1-wA_hE_1 13 - - 0:main - - - -
 [nc_1] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 [disjunct_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_126a>
 #कृपया उत्पाद विवरण की समीक्षा करें ।
 kqpayA 1 - - 3:pof__cn - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 vivaraNa_1 3 - - 5:k2 - - - -
 samIkRA_1 5 - - 6:pof - - - -
 kareM_1-wA_hE_1 6 - - 0:main - - - -
 [NE_0] 8 - - - - - - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_126b>
 #या अधिक जानकारी के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
 aXika_1 1 - - 2:quant - - - -
 jAnakArI_1 2 - - 11:rt - - - -
 $speaker 5 - pl 8:r6 - - - -
 grAhaka_1 6 - - 8:pof__cn - - - -
 sahAyawA_1 7 - - 8:pof__cn - - - -
 ^tIma_1 8 - - 11:k2 - - - -
 saMparka_1 10 - - 11:pof - - - -
 kareM_1-wA_hE_1 11 - - 0:main Ecommerce_FAQ_126a.11:anyawra - - -
 [nc_1] 13 - - - - - - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_127a>
 #कोई उत्पाद हमारी वेबसाइट पर सूचीबद्ध नहीं है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 8:k1 - - - -
 $speaker 3 - pl 4:r6 - - - -
 vebasAita_1 4 - - 8:k7 - - - -
 sUcIbaxXa_1 6 - - 8:k1s - - - -
 nahIM_1 7 - - 8:neg - - - -
 hE_1-pres 8 - - 0:main Ecommerce_FAQ_127b.8:AvaSyakawApariNAma - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_127b>
 #तो यह खरीद के लिए उपलब्ध नहीं हो सकता है।
 $wyax 1 - - 7:k1 - proximal - -
 KarIxa_1 2 - - 7:rt - - - -
 upalabXa_1 5 - - 7:pof - - - -
 nahIM_1 6 - - 7:neg - - - -
 ho_1-0_saka_ho_1 7 - - 0:main - - - -
 [cp_1] 11 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_128>
 #हम उपलब्ध उत्पादों की खोज करने या आगे की सहायता के लिए हमारी ग्राहक सहायता टीम से संपर्क करने की सलाह देते हैं।
 $speaker 1 - pl 0:k1 - - - -
 upalabXa_1 2 - - 3:mod - - - -
 uwpAxa_1 3 - pl 5:k2 - - - -
 Koja_1 5 - - 6:pof - - - -
 kara_1-nA_1 6 - - 0:main - - - -
 AgA_1 8 - pl 10:r6 - - - -
 sahAyawA_1 10 - - 22:rt - - - -
 $speaker 13 - pl 16:r6 - - - -
 grAhaka_1 14 - - 16:pof__cn - - - -
 sahAyawA_1 15 - - 16:pof__cn - - - -
^tIma_1 16 - - 19:k2 - - - -
 saMparka_1 18 - - 19:pof - - - -
 kara_1 19 - pl 21:k2 - - - -
 salAha_1 21 - - 22:pof - - - -
 xe_1-wA_hE_1 22 - - 0:main - - - -
 [nc_1] 25 - - - - - - -
 [cp_1] 26 - - - - - - -
 [cp_2] 27 - - - - - - -
 [cp_3] 28 - - - - - - -
 [disjunct_1] 29 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_129a>
 #कोई उत्पाद 'स्टॉक से बाहर' के रूप में सूचीबद्ध है ।
 koI 1 - - 3:mod - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 stOYka 3 - - 10:k7 - - - -
 bAhara_1 5 - - 3:k7p - - - -
 sUcIbaxXa_1 9 - - 10:k1s - - - -
 hE_1-pres 10 - - 0:main Ecommerce_FAQ_129c.10:AvaSyakawApariNAma - - -
 [nc_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_129b>
 #लेकिन वह बैकऑर्डर के लिए उपलब्ध है ।
 $wyax 1 - - 6:k1 - distal - -
 bEkaOYrdara 2 - - 6:rt - - - -
 upalabXa_1 5 - - 6:k1s - - - -
 hE_1-pres 6 - - 0:main Ecommerce_FAQ_129a.6:viroXI - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_129c>
 #तो आप अपना आइटम सुरक्षित करने के लिए ऑर्डर दे सकते हैं।
 $addressee 1 - - 9:k1 - - - -
 apanA 2 - pl 3:r6 - - - -
 Aitama_1 3 - - 5:k2 - - - -
 surakRiwa_1 4 - - 5:pof - - - -
 kara_1 5 - pl 9:rt - - - -
 OYrdara_1 8 - - 9:k2 - - - -
 xe_1-subj_saka_hE_1 9 - - 0:main - - - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_130>
 #उत्पाद उपलब्ध होने पर भेज दिया जाएगा।
 uwpAxa_1 1 - - 3:k1 - - - -
 upalabXa_1 2 - - 3:pof - - - -
 ho_1 3 - pl 5:rblsk - - - -
 Beja_1-yA_jA_1 5 - - 0:main - [shade:xe_1] - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_131a>
 #यदि किसी उत्पाद को बंडल या सेट के हिस्से के रूप में खरीदा गया था ।
 kisI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 12:k2 - - - -
 baMdala_1 4 - - 8:mod - - - -
 seta_1 6 - - 8:mod - - - -
 hissA_1 8 - pl 12:k7 - - - -
 KarIxa_1-yA_jA_yA1_WA_1 12 - - 0:main Ecommerce_FAQ_131b.12:AvaSyakawApariNAma - - -
 [disjunct_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_131b>
 #तो वापसी नीति भिन्न हो सकती है।
 vApasI_1 1 - - 2:pof__cn - - - -
 nIwi_1 2 - - 4:k1 - - - -
 Binna_1 3 - - 4:pof - - - -
 ho_1-0_saka_ho_1 4 - - 0:main - - - -
 [nc_1] 8 - - - - - - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_132>
 #कृपया विशिष्ट नियम और शर्तों को देखें या आगे के मार्गदर्शन के लिए हमारी ग्राहक सहायता टीम से संपर्क करें।
 kqpayA 1 - - 7:k1 - - - -
 viSiRta_1 2 - - 3:mod - - - -
 niyama_1 3 - - 4:ccof - - - -
 Sarwa_1 5 - pl 4:ccof - - - -
 xeKa_1-e_1 7 - - 0:main - - - -
 AgA_1 9 - pl 11:r6 - - - -
 mArgaxarSana_1 11 - - 20:rt - - - -
 $speaker 14 - pl 17:r6 - - - -
 grAhaka_1 15 - - 17:pof__cn - - - -
 sahAyawA_1 16 - - 17:pof__cn - - - -
^tIma_1 17 - - 20:k2 - - - -
 saMparka_1 19 - - 20:pof - - - -
 kareM_1-wA_hE_1 20 - - 0:main - - - -
 [nc_1] 22 - - - - - - -
 [cp_1] 23 - - - - - - -
 [disjunct_1] 24 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_133>
 #हमारा उद्देश्य जब भी संभव हो लोकप्रिय उत्पादों को फिर से स्टॉक करना है।
 $speaker 1 - pl 2:r6 - - - -
 uxxeSya_1 2 - - 6:k1 - - - -
 $yax 3 - - 6:k7t - - - -
 saMBava_1 5 - - 6:pof - - - -
 ho_1-0_1 6 - - 0:main - - - -
 lokapriya_1 7 - - 8:mod - - - -
 uwpAxa_1 8 - pl 13:k1 - - - -
 Pira_1 10 - - 13:krvn - - - -
 stOYka_1 12 - - 13:pof - - - -
 kara_1 13 - - 6:rc - - - -
 [cp_1] 16 - - - - - - -
 [cp_2] 17 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_134a>
 #कृपया उत्पाद सूचनाओं के लिए साइन अप करें ।
 kqpayA 1 - - 8:k1 - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 sUcanA_1 3 - pl 8:rt - - - -
 sAina_1 6 - - 8:pof - - - -
 apa_1 7 - - 8:pof - - - -
 kareM_1-wA_hE_1 8 - - 0:main - - - -
 [nc_1] 10 - - - - - - -
 [cp_1] 11 - - - - - - -
 [cp_2] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_134b>
 #ताकि जब आइटम फिर से उपलब्ध हो तो आपको सूचित किया जा सके।
 $yax 1 - - 6:k7t - - - -
 Aitama_1 2 - - 6:k1 - - - -
 Pira_1 3 - - 6:krvn - - - -
 upalabXa_1 5 - - 6:pof - - - -
 ho_1 6 - - 7:vmod - - - -
 $addressee 8 - - 10:k2 - - - -
 sUciwa_1 9 - - 10:pof - - - -
 kara_1-yA_jA_1 10 - - 0:main - - - -
 [cp_1] 14 - - - - - - -
 [cp_2] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_135a>
 #कोई उत्पाद 'जल्द ही आ रहा है' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 5:k1 - - - -
 jalxa_1 3 - - 5:krvn - - - -
 A_1 5 - - 12:k7 - - - -
 sUcIbaxXa_1 11 - - 12:k1s - - - -
 hE_1-pres 12 - - 0:main Ecommerce_FAQ_135c.12:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_135b>
 #और वह प्री-ऑर्डर के लिए उपलब्ध है ।
 $wyax 1 - - 6:k1 - distal - -
 prI-OYrdara 2 - - 6:rt - - - -
 upalabXa_1 5 - - 6:k1s - - - -
 hE_1-pres 6 - - 0:main Ecommerce_FAQ_135a.6:samuccaya - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_135c>
 #तो आप अपने आइटम को उपलब्ध होने से पहले सुरक्षित करने के लिए ऑर्डर दे सकते हैं।
 $addressee 1 - - 14:k1 - - - -
 apanA 2 - pl 3:r6 - - - -
 Aitama_1 3 - - 6:k2 - - - -
 upalabXa_1 5 - - 6:pof - - - -
 ho_1 6 - pl 10:rblak - - - -
 pahalA_1 8 - pl 6:k7p - - - -
 surakRiwa_1 9 - - 10:pof - - - -
 kara_1 10 - pl 14:rt - - - -
 OYrdara_1 13 - - 14:k2 - - - -
 xe_1-subj_saka_hE_1 14 - - 0:main - - - -
 [cp_1] 18 - - - - - - -
 [cp_2] 19 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_136a>
 #आपका उत्पाद शिपिंग के दौरान गलत तरीके से हैंडल किए जाने के कारण क्षतिग्रस्त हो गया था ।
 $addressee 1 - - 3:r6 - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 SipiMga_1 3 - - 10:k7a - - - -
 xOrAna_1 5 - - 3:k7p - - - -
 galawa_1 6 - - 7:mod - - - -
 warIkA_1 7 - pl 10:krvn - - - -
 hEMdala_1 9 - - 10:pof - - - -
 kara_1 10 - pl 15:rh - - - -
 kRawigraswa_1 14 - - 15:pof - - - -
 ho_1-yA1_WA_1 15 - - 0:main Ecommerce_FAQ_136b.15:AvaSyakawApariNAma [shade:jA_1] - -
 [nc_1] 19 - - - - - - -
 [cp_1] 20 - - - - - - -
 [cp_2] 21 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_136b>
 #तो कृपया तुरंत हमारी ग्राहक सहायता टीम से संपर्क करें।
 kqpayA 1 - - 9:k1 - - - -
 wuraMwa_1 2 - - 9:krvn - - - -
 $speaker 3 - pl 6:r6 - - - -
 grAhaka_1 4 - - 6:pof__cn - - - -
 sahAyawA_1 5 - - 6:pof__cn - - - -
 ^tIma_1 6 - - 9:ras-k1 - - - -
 saMparka_1 8 - - 9:pof - - - -
 kareM_1-wA_hE_1 9 - - 0:main - - - -
 [nc_1] 11 - - - - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_137>
 #हम वापसी और प्रतिस्थापन के लिए आवश्यक चरणों में आपकी सहायता करेंगे।
 $speaker 1 - pl 12:k1 - - - -
 vApasI_1 2 - - 12:rt - - - -
 prawisWApana_1 4 - - 12:rt - - - -
 AvaSyaka_1 7 - - 8:mod - - - -
 caraNa_1 8 - pl 12:k7 - - - -
 $addressee 10 - - 11:k2 - - - -
 sahAyawA_1 11 - - 12:pof - - - -
 kara_1-gA_1 12 - - 0:main - - - -
 [cp_1] 14 - - - - - - -
 [conj_1] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_138>
 #हम आउट-ऑफ-स्टॉक उत्पादों के लिए आरक्षण प्रदान नहीं करते हैं।
 $speaker 1 - pl 9:k1 - - - -
 Auta-OYPa 2 - - 3:pof__cn - - - -
 uwpAxa_1 3 - pl 9:rt - - - -
 ArakRaNa_1 6 - - 9:k2 - - - -
 praxAna_1 7 - - 9:pof - - - -
 nahIM_1 8 - - 9:neg - - - -
 kara_1-wA_hE_1 9 - - 0:main - - - -
 [nc_1] 12 - - - - - - -
 [cp_1] 13 - - - - - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_139a>
 #हालाँकि, आप उत्पाद सूचनाओं के लिए साइन अप कर सकते हैं ।
 $addressee 2 - - 9:k1 - - - -
 uwpAxa_1 3 - - 4:pof__cn - - - -
 sUcanA_1 4 - pl 9:rt - - - -
 sAina_1 7 - - 9:k2 - - - -
 apa_1 8 - - 9:pof - - - -
 kara_1-0_saka_hE_1 9 - - 0:main - - - -
 [nc_1] 13 - - - - - - -
 [cp_1] 14 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_139b>
 #ताकि आइटम के फिर से उपलब्ध होने पर आपको सूचित किया जा सके।
 Aitama_1 1 - - 6:k1 - - - -
 Pira_1 3 - - 6:krvn - - - -
 upalabXa_1 5 - - 6:pof - - - -
 ho_1 6 - pl 10:rblsk - - - -
 $addressee 8 - - 10:k2 - - - -
 sUciwa_1 9 - - 10:pof - - - -
 kara_1-yA_jA_1 10 - - 0:main - - - -
 [cp_1] 14 - - - - - - -
 [cp_2] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_140a>
 #कोई उत्पाद 'प्री-ऑर्डर' के रूप में सूचीबद्ध है ।
 koI 1 - - 3:mod - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 prI-OYrdara 3 - - 8:k7 - - - -
 sUcIbaxXa_1 7 - - 8:k1s - - - -
 hE_1-pres 8 - - 0:main Ecommerce_FAQ_140c.8:AvaSyakawApariNAma - - -
 [nc_1] 10 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_140b>
 #और कोई बैकऑर्डर के लिए उपलब्ध है ।
 koI 1 - - 2:mod - - - -
 bEkaOYrdara_1 2 - - 6:rt - - - -
 upalabXa_1 5 - - 6:k1s - - - -
 hE_1-pres 6 - - 0:main Ecommerce_FAQ_140a.6:samuccaya - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_140c>
 #तो आप अपना आइटम सुरक्षित करने के लिए ऑर्डर दे सकते हैं।
 $addressee 1 - - 9:k1 - - - -
 apanA 2 - pl 3:r6 - - - -
 Aitama_1 3 - - 5:k2 - - - -
 surakRiwa_1 4 - - 5:pof - - - -
 kara_1 5 - pl 9:rt - - - -
 OYrdara_1 8 - - 9:k2 - - - -
 xe_1-subj_saka_hE_1 9 - - 0:main - - - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_141>
 #उत्पाद उपलब्ध होने पर भेज दिया जाएगा।
 uwpAxa_1 1 - - 3:k1 - - - -
 upalabXa_1 2 - - 3:pof - - - -
 ho_1 3 - pl 5:rblsk - - - -
 Beja_1-yA_jA_1 5 - - 0:main - [shade:xe_1] - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_142>
 #हाँ, आप स्टोर क्रेडिट से खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 11:k1 - - - -
 stora_1 3 - - 4:pof__cn - - - -
 kredita_1 4 - - 6:k5 - - - -
 KarIxa_1 6 - - 8:rbks - - - -
 uwpAxa_1 8 - - 11:k2 - - - -
 vApasa_1 10 - - 11:pof - - - -
 kara_1-0_saka_hE_1 11 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [cp_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_143>
 #रिफ़ंड स्टोर क्रेडिट के रूप में जारी किया जाएगा, जिसका उपयोग आप भविष्य की खरीदारी के लिए कर सकते हैं।
 riPZMda_1 1 - - 3:pof__cn - - - -
 stora_1 2 - - 3:pof__cn - - - -
 kredita_1 3 - - 8:k7 - - - -
 jArI_1 7 - - 8:pof - - - -
 kara_1 8 - - 18:vmod - - - -
 $yax 10 - - 11:k2 - - - -
 upayoga_1 11 - - 18:k2 - - - -
 $addressee 12 - - 18:k1 - - - -
 BaviRya_1 13 - - 15:r6 - - - -
 KarIxArI_1 15 - - 18:rt - - - -
 kara_1-yA_saka_hE_1 18 - - 0:main - - - -
 [nc_1] 22 - - - - - - -
 [cp_1] 23 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_144>
 #हम जब भी संभव हो लोकप्रिय उत्पादों को फिर से स्टॉक करने का प्रयास करते हैं।
 $speaker 1 - pl 15:k1 - - - -
 $yax 2 - - 5:k7t - - - -
 saMBava_1 4 - - 5:pof - - - -
 ho_1 5 - - 15:vmod - - - -
 lokapriya_1 6 - - 7:mod - - - -
 uwpAxa_1 7 - pl 12:k2 - - - -
 Pira_1 9 - - 12:krvn - - - -
 stOYka_1 11 - - 12:pof - - - -
 kara_1 12 - pl 14:k2 - - - -
 prayAsa_1 14 - - 15:pof - - - -
 kara_1-wA_hE_1 15 - - 0:main - - - -
 [cp_1] 18 - - - - - - -
 [cp_2] 19 - - - - - - -
 [cp_3] 20 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_145a>
 #कृपया उत्पाद सूचनाओं के लिए साइन अप करें ।
 kqpayA 1 - - 8:k1 - - - -
 uwpAxa_1 2 - - 3:pof__cn - - - -
 sUcanA_1 3 - pl 8:rt - - - -
 sAina_1 6 - - 8:pof - - - -
 apa_1 7 - - 8:pof - - - -
 kareM_1-wA_hE_1 8 - - 0:main - - - -
 [nc_1] 10 - - - - - - -
 [cp_1] 11 - - - - - - -
 [cp_2] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_145b>
 #ताकि जब आइटम फिर से उपलब्ध हो तो आपको सूचित किया जा सके।
 $yax 1 - - 6:k7t - - - -
 Aitama_1 2 - - 6:k1 - - - -
 Pira_1 3 - - 6:krvn - - - -
 upalabXa_1 5 - - 6:pof - - - -
 ho_1 6 - - 7:vmod - - - -
 $addressee 8 - - 10:k2 - - - -
 sUciwa_1 9 - - 10:pof - - - -
 kara_1-yA_jA_1 10 - - 0:main - - - -
 [cp_1] 14 - - - - - - -
 [cp_2] 15 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_146a>
 #कोई उत्पाद 'बिक चुका है' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 3:k1 - - - -
 bika_1 3 - - 10:k7 - - - -
 sUcIbaxXa_1 9 - - 10:k1s - - - -
 hE_1-pres 10 - - 0:main Ecommerce_FAQ_146c.10:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_146b>
 #लेकिन वह प्री-ऑर्डर के लिए उपलब्ध है ।
 $wyax 1 - - 6:k1 - distal - -
 prI-OYrdara 2 - - 6:rt - - - -
 upalabXa_1 5 - - 6:k1s - - - -
 hE_1-pres 6 - - 0:main Ecommerce_FAQ_146a.6:viroXI - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_146c>
 #तो आप अपना आइटम सुरक्षित करने के लिए ऑर्डर दे सकते हैं।
 $addressee 1 - - 9:k1 - - - -
 apanA 2 - pl 3:r6 - - - -
 Aitama_1 3 - - 5:k2 - - - -
 surakRiwa_1 4 - - 5:pof - - - -
 kara_1 5 - pl 9:rt - - - -
 OYrdara_1 8 - - 9:k2 - - - -
 xe_1-subj_saka_hE_1 9 - - 0:main - - - -
 [cp_1] 13 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_147>
 #उत्पाद उपलब्ध होने पर भेज दिया जाएगा।
 uwpAxa_1 1 - - 3:k1 - - - -
 upalabXa_1 2 - - 3:pof - - - -
 ho_1 3 - pl 5:rblsk - - - -
 Beja_1-yA_jA_1 5 - - 0:main - [shade:xe_1] - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_148>
 #हाँ, आप प्रचारात्मक उपहार कार्ड से खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 7:k1 - - - -
 pracArAwmaka_1 3 - - 4:mod - - - -
 upahAra_1 4 - - 7:k2 - - - -
 kArda_1 5 - - 7:k5 - - - -
 KarIxa_1 7 - - 9:rbks - - - -
 uwpAxa_1 9 - - 12:k2 - - - -
 vApasa_1 11 - - 12:pof - - - -
 kara_1-0_saka_hE_1 12 - - 0:main - - - -
 [cp_1] 16 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_149>
 #रिफ़ंड स्टोर क्रेडिट या नए उपहार कार्ड के रूप में जारी किया जाएगा।
 riPZMda_1 1 - - 3:pof__cn - - - -
 stora_1 2 - - 3:pof__cn - - - -
 kredita_1 3 - - 12:k2 - - - -
 nae_1 5 - - 7:mod - - - -
 upahAra_1 6 - - 7:pof__cn - - - -
 kArda_1 7 - - 12:k2 - - - -
 jArI_1 11 - - 12:pof - - - -
 kara_1-yA_jA_gA_1 12 - - 0:main - - - -
 [nc_1] 15 - - - - - - -
 [nc_2] 16 - - - - - - -
 [cp_1] 17 - - - - - - -
 [disjunct_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_150a>
 #कोई उत्पाद आपके पसंदीदा रंग में उपलब्ध नहीं है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 9:k1 - - - -
 $addressee 3 - - 5:r6 - - - -
 pasaMxIxA_1 4 - - 5:mod - - - -
 raMga_1 5 - - 9:k7 - - - -
 upalabXa_1 7 - - 9:k1s - - - -
 nahIM_1 8 - - 9:neg - - - -
 hE_1-pres 9 - - 0:main Ecommerce_FAQ_150b.9:AvaSyakawApariNAma - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_150b>
 #तो वह अस्थायी रूप से स्टॉक से बाहर हो सकता है।
 $wyax 1 - - 8:k1 - distal - -
 asWAyI_1 2 - - 3:mod - - - -
 rUpa_1 3 - - 8:krvn - - - -
 stOYka_1 5 - - 8:k5 - - - -
 bAhara_1 7 - - 8:pof - - - -
 ho_1-0_saka_ho_1 8 - - 0:main - - - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_151a>
 #कृपया बाद में फिर से जाँच करें ।
 kqpayA 1 - - 7:k1 - - - -
 bAxa_1 2 - - 7:k7t - - - -
 Pira_1 4 - - 7:krvn - - - -
 jAzca_1 6 - - 7:pof - - - -
 kareM_1-wA_hE_1 7 - - 0:main - - - -
 [cp_1] 9 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_151b>
 #या रंग सूचनाओं के लिए साइन अप करें।
 raMga_1 1 - pl 2:pof__cn - - - -
 sUcanA_1 2 - pl 7:rt - - - -
 sAina_1 5 - - 7:pof - - - -
 apa_1 6 - - 7:pof - - - -
 kareM_1-wA_hE_1 7 - - 0:main Ecommerce_FAQ_151a.7:anyawra - - -
 [nc_1] 9 - - - - - - -
 [cp_1] 10 - - - - - - -
 [cp_2] 11 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_152a>
 #कोई उत्पाद 'जल्द ही आ रहा है' के रूप में सूचीबद्ध है ।
 koI 1 - - 2:mod - - - -
 uwpAxa_1 2 - - 5:k1 - - - -
 jalxa_1 3 - - 5:krvn - - - -
 A_1 5 - - 12:k7 - - - -
 sUcIbaxXa_1 11 - - 12:k1s - - - -
 hE_1-pres 12 - - 0:main Ecommerce_FAQ_152e.12:AvaSyakawApariNAma - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_152b>
 #लेकिन वह प्री-ऑर्डर के लिए उपलब्ध नहीं है ।
 $wyax 1 - - 7:k1 - distal - -
 prI-OYrdara 2 - - 7:rt - - - -
 upalabXa_1 5 - - 7:k1s - - - -
 nahIM_1 6 - - 7:neg - - - -
 hE_1-pres 7 - - 0:main Ecommerce_FAQ_152a.7:viroXI - - -
 %negative
 </sent_id>
<sent_id=Ecommerce_FAQ_152c>
 #तो आपको तब तक प्रतीक्षा करनी होगी ।
 $addressee 1 - - 5:k1 - - - -
 waba 2 - - 5:k7t - - - -
 prawIkRA_1 4 - - 5:pof - - - -
 kara_1-nA_ho_1 5 - - 0:main - - - -
 [cp_1] 8 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_152d>
 #जब तक कि वह आधिकारिक रूप से जारी न हो जाए ।
 $wyax 3 - - 9:k1 - distal - -
 AXikArika_1 4 - - 5:mod - - - -
 rUpa_1 5 - - 9:krvn - - - -
 jArI_1 7 - - 9:pof - - - -
 na_1 8 - - 9:neg - - - -
 ho_1-e_1 9 - - 0:main - [shade:jA_1] - -
 [cp_1] 12 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_152e>
 #और वह खरीद के लिए उपलब्ध न हो जाए।
 $wyax 1 - - 7:k1 - distal - -
 KarIxa_1 2 - - 7:rt - - - -
 upalabXa_1 5 - - 7:pof - - - -
 na_1 6 - - 7:neg - - - -
 ho_1-e_1 7 - - 0:main Ecommerce_FAQ_152d.7:samuccaya [shade:jA_1] - -
 [cp_1] 10 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_153>
 #हाँ, आप किसी प्रचार कार्यक्रम के दौरान खरीदे गए उत्पाद को वापस कर सकते हैं।
 hAz, 1 - - 0:mod - - - -
 $addressee 2 - - 13:k1 - - - -
 kisI 3 - - 5:mod - - - -
 pracAra_1 4 - - 5:pof__cn - - - -
 kAryakrama_1 5 - - 8:k7t - - - -
 xOrAna_1 7 - - 5:k7p - - - -
 KarIxa_1 8 - - 10:rbks - - - -
 uwpAxa_1 10 - - 13:k2 - - - -
 vApasa_1 12 - - 13:pof - - - -
 kara_1-0_saka_hE_1 13 - - 0:main - - - -
 [nc_1] 17 - - - - - - -
 [cp_1] 18 - - - - - - -
 %affirmative
 </sent_id>
<sent_id=Ecommerce_FAQ_154>
 #किसी भी लागू छूट के बाद भुगतान की गई राशि के आधार पर रिफ़ंड संसाधित किया जाएगा।
 kisI 1 - - 4:mod - - - -
 lAgU_1 3 - - 4:mod - - - -
 CUta_1 4 - - 8:k7t - - - -
 bAxa_1 6 - - 4:k7p - - - -
 BugawAna_1 7 - - 8:pof - - - -
 kara_1 8 - - 10:rbks - - - -
 rASi_1 10 - - 12:r6 - - - -
 AXAra_1 12 - - 16:k7 - - - -
 riPZMda_1 14 - - 16:k2 - - - -
 saMsAXiwa_1 15 - - 16:pof - - - -
 kara_1-yA_jA_gA_1 16 - - 0:main - - - -
 [cp_1] 19 - - - - - - -
 [cp_2] 20 - - - - - - -
 %affirmative
 </sent_id>



















""",
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
