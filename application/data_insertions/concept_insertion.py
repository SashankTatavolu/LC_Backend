from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Updated table schema
class ConceptDictionary(Base):
    __tablename__ = 'concept_dictionary'

    concept_id = Column(Integer, primary_key=True)
    concept_label = Column(String(255), nullable=False)  # Concept Label
    hindi_label = Column(String(255), nullable=False)    # Hindi Label
    sanskrit_label = Column(String(255), nullable=True)  # Sanskrit Label (nullable)
    english_label = Column(String(255), nullable=False)  # English Label
    mrsc = Column(String(255), nullable=True)            # MRSC (nullable)

def read_concepts_from_file(file_path):
    concepts = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().strip('()').split()
            if len(parts) >= 5:
                concept_label = parts[0]
                hindi_label = parts[1]
                sanskrit_label = parts[2]
                english_label = parts[3]
                mrsc = parts[4]
                concepts.append({
                    'concept_label': concept_label,
                    'hindi_label': hindi_label,
                    'sanskrit_label': sanskrit_label,
                    'english_label': english_label,
                    'mrsc': mrsc
                })
    return concepts

# Update the DATABASE_URL as needed
DATABASE_URL = 'postgresql://postgres:Sashank123@localhost/testdb'
# DATABASE_URL = 'postgresql://postgres:password123@10.2.8.12/lc4u'

engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)

session = Session()

# Create table with the new schema
Base.metadata.create_all(engine)

concept_file_path = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/data/concept-to-mrs-rels.dat'

# Read concepts from the updated file format
concepts = read_concepts_from_file(concept_file_path)

# Insert concepts into the database
for concept_data in concepts:
    new_concept = ConceptDictionary(**concept_data)
    session.add(new_concept)

session.commit()

print("Concept data inserted successfully.")
