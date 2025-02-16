from application.extensions import db

class ConceptSubmission(db.Model):
    __tablename__ = 'concept_submissions'

    id = db.Column(db.Integer, primary_key=True)  # Auto increment primary key
    user_id = db.Column(db.String(255), nullable=False)  # User ID submitting the concept
    from_email = db.Column(db.String(255), nullable=False)  # Email of the user submitting
    to_email = db.Column(db.String(255), nullable=False)  # Recipient's email
    hindi_concept = db.Column(db.Text, nullable=False)  # Hindi concept text
    english_concept = db.Column(db.Text, nullable=False)  # English concept text
    concept_id = db.Column(db.String(255), nullable=False)  # Concept ID
    sentence_id = db.Column(db.String(255), nullable=False)  # Sentence ID
    sentence = db.Column(db.Text, nullable=False)  # Sentence text
    english_sentence = db.Column(db.Text, nullable=False) 
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Timestamp when record was created

    def __repr__(self):
        return f"<ConceptSubmission {self.concept_id} by {self.user_id}>"
