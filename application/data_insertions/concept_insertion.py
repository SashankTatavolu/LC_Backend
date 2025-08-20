import csv
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
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            concepts.append({
                'concept_label': row['concept_label'],
                'hindi_label': row['hindi_label'],
                'sanskrit_label': row.get('sanskrit_label'),  # handles optional
                'english_label': row['english_label'],
                'mrsc': row.get('mrsc')  # handles optional
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

concept_file_path = '/home/sashank/Downloads/cleaned_concept_dictionary.csv'

# Read concepts from the updated file format
concepts = read_concepts_from_file(concept_file_path)

# Insert concepts into the database
for concept_data in concepts:
    new_concept = ConceptDictionary(**concept_data)
    session.add(new_concept)

session.commit()

print("Concept data inserted successfully.")
