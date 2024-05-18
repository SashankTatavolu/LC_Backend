from ..models.user_model import User, db

class UserService:

    @staticmethod
    def create_user(data):
        user = User(
            username=data['username'],
            role=data['role']
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
