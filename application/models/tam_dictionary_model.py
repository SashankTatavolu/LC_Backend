from application.extensions import db

class TAM_Dictionary(db.Model):
    __tablename__ = 'tam_dictionary'

    id = db.Column(db.Integer, primary_key=True)
    u_tam = db.Column(db.String(255), nullable=False)
    hindi_tam = db.Column(db.String(255), nullable=False)
    sanskrit_tam = db.Column(db.String(255), nullable=True)
    english_tam = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<TAM_Dictionary {self.entry_id}: {self.u_tam}>'