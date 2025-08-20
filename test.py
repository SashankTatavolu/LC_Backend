from sqlalchemy import create_engine, func, and_, not_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

# Replace with your actual DB URL
DATABASE_URL = "postgresql://postgres:password123@10.2.8.12/lc4u"

Base = declarative_base()

# Models (only relevant fields)
class Chapter(Base):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True)

class Sentence(Base):
    __tablename__ = 'sentences'
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))

class Segment(Base):
    __tablename__ = 'segments'
    segment_id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))

class LexicalConceptual(Base):
    __tablename__ = 'lexical_conceptual'
    lexical_conceptual_id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('segments.segment_id'))
    concept = Column(String(255), nullable=False)
    semantic_category = Column(String(255))
    morpho_semantics = Column(String(255))
    speakers_view = Column(String(255))

# DB setup
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get all chapter IDs
chapter_ids = session.query(Chapter.id).all()

print("\n📊 Chapter-Level Stats:\n")

for (chapter_id,) in chapter_ids:
    # Sentence count
    sentence_count = session.query(func.count(Sentence.id)).filter(Sentence.chapter_id == chapter_id).scalar()

    # Segment IDs in chapter
    segment_ids_query = session.query(Segment.segment_id).filter(Segment.chapter_id == chapter_id).subquery()

    # Segment count
    segment_count = session.query(func.count()).select_from(segment_ids_query).scalar()

    # Total Concepts
    total_concepts = session.query(func.count()).filter(LexicalConceptual.segment_id.in_(segment_ids_query)).scalar()

    # Complex Concepts (concept like '[%]')
    complex_concepts = session.query(func.count()).filter(
        LexicalConceptual.segment_id.in_(segment_ids_query),
        LexicalConceptual.concept.like('[%]')
    ).scalar()

    # semantic_category ≠ '-'
    semcat_count = session.query(func.count()).filter(
        LexicalConceptual.segment_id.in_(segment_ids_query),
        LexicalConceptual.semantic_category != '-'
    ).scalar()

    # morpho_semantics ≠ '-'
    morpho_count = session.query(func.count()).filter(
        LexicalConceptual.segment_id.in_(segment_ids_query),
        LexicalConceptual.morpho_semantics != '-'
    ).scalar()

    # speakers_view ≠ '-'
    speaker_view_count = session.query(func.count()).filter(
        LexicalConceptual.segment_id.in_(segment_ids_query),
        LexicalConceptual.speakers_view != '-'
    ).scalar()

    print(f"📘 Chapter ID: {chapter_id}")
    print(f"  ➤ Sentence Count        : {sentence_count}")
    print(f"  ➤ Segment Count         : {segment_count}")
    print(f"  ➤ Total Concepts        : {total_concepts}")
    print(f"  ➤ Complex Concepts      : {complex_concepts}")
    print(f"  ➤ Semantic Categories   : {semcat_count}")
    print(f"  ➤ Morpho-Semantics      : {morpho_count}")
    print(f"  ➤ Speakers' View        : {speaker_view_count}")
    print("")

session.close()
