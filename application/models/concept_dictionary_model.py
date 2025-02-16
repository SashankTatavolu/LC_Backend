from application.extensions import db

class ConceptDictionary(db.Model):
    __tablename__ = 'concept_dictionary'

    concept_id = db.Column(db.Integer, primary_key=True)
    concept_label = db.Column (db.String(255), nullable= False)
    hindi_label = db.Column(db.String(255), nullable=False)
    sanskrit_label = db.Column(db.String(255), nullable=True)
    english_label = db.Column(db.String(255), nullable=False)
    mrsc =db.Column(db.String(255), nullable=True)
    
