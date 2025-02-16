from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password123@10.2.8.12/lc4u')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    organization = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def total_assigned_projects(self):
        if self.role in ['annotator', 'reviewer']:
            return self.projects.count()
        return 0
    
    def total_uploaded_projects(self):
        if self.role == 'admin':
            return self.projects_uploaded.count()
        return 0

def create_users():
    with app.app_context():
        users = [
            # {'username': 'Ismaanwar', 'email': 'ismaanwar97@gmail.com', 'role': 'annotator', 'organization': 'IIITH', 'password': 'Ismaanwar123'},
            # {'username': 'arjun', 'email': 'arjun.rs.hss22@itbhu.ac.in', 'role': 'annotator', 'organization': 'IITBHU', 'password': 'Arjun123'},
            # {'username': 'bidishab', 'email': 'bidishab.du@gmail.com', 'role': 'annotator', 'organization': 'IIITH', 'password': 'Bidishab123'},
            # {'username': 'manu', 'email': 'manu.mashani@gmail.com', 'role': 'annotator', 'organization': 'IITBHU', 'password': 'Manumashani123'},
            # {'username': 'sharmarajni', 'email': 'sharmarajni342@gmail.com', 'role': 'annotator', 'organization': 'IITBHU', 'password': 'Sharmarajni123'},
            # {'username': 'sudarshangautam', 'email': 'sudarshangautam.rs.hss22@itbhu.ac.in', 'role': 'annotator', 'organization': 'IITBHU', 'password': 'sudarshangautam123'},
            # {'username': 'Somapaul', 'email': 'somapauls@gmail.com', 'role': 'admin', 'organization': 'IIITH', 'password': 'Somapaul123'},
            # {'username': 'Sukhada', 'email': 'sukhada.hss@iitbhu.ac.in', 'role': 'admin', 'organization': 'IITBHU', 'password': 'Sukhada123'},
              {'username': 'tejaswi', 'email': 'tejaswipoppoppu@gmail.com', 'role': 'dictionaryValidator', 'organization': 'IIITH', 'password': 'tejaswi'},


        ]

        for user_data in users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                organization=user_data.get('organization', None)
            )
            user.set_password(user_data['password'])

            db.session.add(user)

        db.session.commit()

        print(f"{len(users)} users have been successfully created and added to the database.")

if __name__ == '__main__':
    create_users()
