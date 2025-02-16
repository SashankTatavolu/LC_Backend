# import re
# from sqlalchemy import Boolean, create_engine, Column, Integer, String, Text, DateTime, ForeignKey
# from sqlalchemy.orm import sessionmaker, declarative_base, relationship
# import datetime

# # Database configuration
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc'
# engine = create_engine(SQLALCHEMY_DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# class Chapter(Base):
#     __tablename__ = 'chapters'
#     id = Column(Integer, primary_key=True)
#     project_id = Column(Integer, nullable=False)
#     name = Column(String(255), nullable=False)
#     uploaded_by_id = Column(Integer, nullable=False)
#     text = Column(Text, nullable=False)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# class Sentence(Base):
#     __tablename__ = "sentences"
#     id = Column(Integer, primary_key=True, index=True)
#     chapter_id = Column(Integer, ForeignKey('chapters.id'))
#     sentence_index = Column(String, index=True)
#     sentence_id = Column(String, nullable=False, unique=True)
#     text = Column(Text)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
#     segments = relationship("Segment", back_populates="sentence")

# # Segment model
# class Segment(Base):
#     __tablename__ = 'segments'
#     segment_id = Column(Integer, primary_key=True)
#     sentence_id = Column(Integer, ForeignKey('sentences.id'), nullable=False)
#     segment_index = Column(String(50))
#     segment_text = Column(Text, nullable=False)
#     segment_type = Column(String(50))
#     index_type = Column(String(20), nullable=False)
#     sentence = relationship("Sentence", back_populates="segments")
#     relational = relationship('Relational', back_populates='segment')
#     construction = relationship("Construction", back_populates="segment")
#     discourse = relationship("Discourse", back_populates="segment")
#     # domain_terms = relationship('DomainTerm', back_populates='segment')

# class LexicalConceptual(Base):
#     __tablename__ = 'lexical_conceptual'
#     lexical_conceptual_id = Column(Integer, primary_key=True)
#     segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
#     index = Column(Integer, nullable=False)
#     concept = Column(String(255), nullable=False)
#     relational = relationship('Relational', back_populates='concept')
#     constructions = relationship('Construction', back_populates='concept')
#     discourse = relationship('Discourse', back_populates='concept')
#     # domain_terms = relationship('DomainTerm', back_populates='concept')

# class Relational(Base):
#     __tablename__ = 'relational'
#     relational_id = Column(Integer, primary_key=True)
#     segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
#     segment_index = Column(String(50), nullable=False)
#     index = Column(Integer)  # Added index column
#     # cxn_index = Column(Integer)  # Changed column name here
#     component_type = Column(String(255), nullable=False)
#     main_index = Column(String(255))  # Added main_index column
#     relation = Column(String(255))  # Added relation column
#     is_main = Column(Boolean, default=False)
#     concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)  # Added concept_id column
#     segment = relationship('Segment', back_populates='relational')
#     concept = relationship('LexicalConceptual', back_populates='relational')

# # Construction model
# class Construction(Base):
#     __tablename__ = 'construction'
#     construction_id = Column(Integer, primary_key=True)
#     segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
#     segment_index = Column(String(50), nullable=False)
#     index = Column(Integer)  # Added index column
#     cxn_index = Column(String(50))  # Added cxn_index column
#     component_type = Column(String(255))  # Added component_type column
#     concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)  # Added concept_id column
#     construction = Column(String(50), nullable=False)
#     segment = relationship('Segment', back_populates='construction')
#     concept = relationship('LexicalConceptual', back_populates='constructions')

#     def serialize(self):
#         return {
#             'construction_id': self.construction_id,
#             'segment_id': self.segment_id,
#             'segment_index': self.segment_index,
#             'index': self.index,  # Include index in serialization
#             'cxn_index': self.cxn_index,  # Include cxn_index in serialization
#             'component_type': self.component_type,  # Include component_type in serialization
#             'concept_id': self.concept_id,  # Include concept_id in serialization
#             'construction': self.construction
#         }

# # Discourse model
# class Discourse(Base):
#     __tablename__ = 'discourse'
#     discourse_id = Column(Integer, primary_key=True)
#     segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
#     segment_index = Column(String(50), nullable=False)
#     discourse = Column(String(50))
#     index = Column(Integer) 
#     head_index = Column(String(50))  
#     relation = Column(String(255)) 
#     segment = relationship('Segment', back_populates='discourse')
#     concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True) 
#     concept = relationship('LexicalConceptual', back_populates='discourse')

#     def serialize(self):
#         return {
#             'discourse_id': self.discourse_id,
#             'segment_id': self.segment_id,
#             'segment_index': self.segment_index,
#             'index': self.index, 
#             'head_index': self.head_index,
#             'relation': self.relation,
#             'concept_id': self.concept_id, 
#             'discourse': self.discourse
#         }

# # class DomainTerm(Base):
# #     __tablename__ = 'domain_terms'
# #     domain_term_id = Column(Integer, primary_key=True)
# #     segment_id = Column(Integer, ForeignKey('segments.segment_id'), nullable=False)
# #     segment_index = Column(String(50), nullable=False)
# #     index = Column(Integer, nullable=False)
# #     domain_term = Column(String(255))
# #     concept_id = Column(Integer, ForeignKey('lexical_conceptual.lexical_conceptual_id'), nullable=True)
# #     segment = relationship('Segment', back_populates='domain_terms')
# #     concept = relationship('LexicalConceptual', back_populates='domain_terms')

# # Create tables
# # Base.metadata.create_all(bind=engine)

# # def parse_data_for_domain_terms(file_path):
# #     domain_terms = []
# #     current_segment_id = None

# #     with open(file_path, 'r', encoding='utf-8') as file:
# #         lines = file.readlines()

# #     for line in lines:
# #         line = line.strip()
# #         if line.startswith("<sent_id="):
# #             match = re.search(r'<sent_id\s*=\s*([\w_\-]+)>', line)
# #             if match:
# #                 current_segment_id = match.group(1)
# #             else:
# #                 current_segment_id = None
# #         elif line.startswith("</sent_id>"):
# #             current_segment_id = None
# #         elif line.startswith("#") or line.startswith("%") or line.startswith("*"):
# #             continue  # Skip comments and other markers
# #         elif line and current_segment_id is not None:
# #             parts = re.split(r'\s+', line)
# #             if len(parts) >= 8:  # Ensure there are at least 8 columns (domain term in the 8th column)
# #                 try:
# #                     index = int(parts[1])
# #                     domain_term = parts[7]  # Extract the 8th column for domain_term

# #                     domain_terms.append({
# #                         'segment_id': current_segment_id,
# #                         'index': index,
# #                         'domain_term': domain_term
# #                     })
# #                 except ValueError:
# #                     print(f"Error: Invalid format in line: {line}")
# #             else:
# #                 print(f"Error: Unexpected format in line: {line}")

# #     return domain_terms

# # def insert_domain_term_data(session, file_path, chapter_id):
# #     try:
# #         domain_term_data = parse_data_for_domain_terms(file_path)

# #         for domain_data_item in domain_term_data:
# #             segment_id = domain_data_item['segment_id']
# #             # Find segment by segment_index
# #             # segment = session.query(Segment).filter_by(segment_index=domain_data_item['segment_id']).first()
# #             segment = session.query(Segment).join(Sentence).filter(
# #                     Segment.segment_index == segment_id,
# #                     Sentence.chapter_id == chapter_id
# #                 ).first()

# #             if segment:
# #                 # Find the lexical_conceptual_id using the segment_id and index
# #                 lexical_concept = session.query(LexicalConceptual).filter_by(
# #                     segment_id=segment.segment_id,
# #                     index=domain_data_item['index']
# #                 ).first()

# #                 concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None
# #                 if(domain_data_item['domain_term']!="-"):
# #                     print(concept_id, domain_data_item['index'], domain_data_item['domain_term'], domain_data_item['segment_id'])

# #                 #Insert domain term
# #                 domain_term = DomainTerm(
# #                     segment_id=segment.segment_id,
# #                     segment_index=domain_data_item['segment_id'],
# #                     index=domain_data_item['index'],
# #                     domain_term=domain_data_item['domain_term'],
# #                     concept_id=concept_id
# #                 )
# #                 session.add(domain_term)
# #             else:
# #                 print(f"Error: No matching segment found for segment_index: {domain_data_item['segment_id']}")

# #         session.commit()
# #         print("Domain term data inserted successfully!")

# #     except Exception as e:
# #         print(f"Error inserting domain term data: {e}")
# #         session.rollback()

# #     finally:
# #         session.close()
# #         print("done")

# # def insert_domain_term_data(session, file_path, chapter_id):
# #     try:
# #         domain_term_data = parse_data_for_domain_terms(file_path)

# #         for domain_data_item in domain_term_data:
# #             segment_id = domain_data_item['segment_id']
            
# #             # Find segment by segment_index
# #             segment = session.query(Segment).join(Sentence).filter(
# #                 Segment.segment_index == segment_id,
# #                 Sentence.chapter_id == chapter_id
# #             ).first()

# #             if segment:
# #                 # Find the lexical_conceptual_id using the segment_id and index
# #                 lexical_concept = session.query(LexicalConceptual).filter_by(
# #                     segment_id=segment.segment_id,
# #                     index=domain_data_item['index']
# #                 ).first()

# #                 concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

# #                 # Check if domain term already exists for this segment, index, and if it's not "-"
# #                 existing_domain_term = session.query(DomainTerm).filter_by(
# #                     segment_index=domain_data_item['segment_id'],
# #                     index=domain_data_item['index'],
# #                     domain_term=domain_data_item['domain_term']
# #                 ).first()

# #                 if existing_domain_term:
# #                     print(f"Skipping existing domain term for segment_index: {domain_data_item['segment_id']}, index: {domain_data_item['index']}")
# #                     continue

# #                 if domain_data_item['domain_term'] != "-":
# #                     print(concept_id, domain_data_item['index'], domain_data_item['domain_term'], domain_data_item['segment_id'])

# #                 # Insert new domain term
# #                 domain_term = DomainTerm(
# #                     segment_id=segment.segment_id,
# #                     segment_index=domain_data_item['segment_id'],
# #                     index=domain_data_item['index'],
# #                     domain_term=domain_data_item['domain_term'],
# #                     concept_id=concept_id
# #                 )
# #                 session.add(domain_term)
# #             else:
# #                 print(f"Error: No matching segment found for segment_index: {domain_data_item['segment_id']}")

# #         session.commit()
# #         print("Domain term data inserted successfully!")

# #     except Exception as e:
# #         print(f"Error inserting domain term data: {e}")
# #         session.rollback()

# #     finally:
# #         session.close()
# #         print("done")


# def main():
#     file_path = "/home/eswarkartheek/Downloads/oct4/Language_Communicator_Backend/application/data_insertions/sanskrit data/sanskrit_data (1).txt"  
#     chapter_id = 20
#     session = SessionLocal()
#     insert_domain_term_data(session, file_path, chapter_id)

# if __name__ == "__main__":
#     main()