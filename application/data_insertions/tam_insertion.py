import psycopg2
from psycopg2 import sql
import csv

# Database connection parameters
DB_NAME = "testdb"
DB_USER = "postgres"
DB_PASSWORD = "Sashank123"
DB_HOST = "localhost"  # or your database host
DB_PORT = "5432"  # default PostgreSQL port

# TSV file path
TSV_FILE = "/home/sashank/Downloads/tam_morph_tuple.tsv"

def insert_data():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Create table if not exists (optional)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tam_dictionary (
                id SERIAL PRIMARY KEY,
                u_tam VARCHAR(255) NOT NULL,
                hindi_tam VARCHAR(255) NOT NULL,
                sanskrit_tam VARCHAR(255),
                english_tam VARCHAR(255) NOT NULL
            )
        """)

        # Read and insert data from TSV
        with open(TSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                cursor.execute("""
                    INSERT INTO tam_dictionary (
                        id, u_tam, hindi_tam, sanskrit_tam, english_tam
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    )
                """, (
                    row['concept_id'],
                    row['U_TAM'],
                    row['Hindi_TAM'],
                    row['sanskrit_Tam'] if row['sanskrit_Tam'] else None,  # Handle empty values
                    row['English_Tam']
                ))

        # Commit changes
        conn.commit()
        print("Data inserted successfully!")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    insert_data()