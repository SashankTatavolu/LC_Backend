from sqlalchemy import String, cast, func
from ..models.user_model import User, db

class UserService:
    
    @staticmethod
    def create_user(data):
        if not data.get('username') or not data.get('role') or not data.get('password') or not data.get('organization') or not data.get('email'):
            return None

        # Ensure role is a list (you already handle this in the route, so this step might be redundant)
        if not isinstance(data['role'], list):
            data['role'] = [role.strip() for role in data['role'].split(',')]

        # Create user instance
        user = User(
            username=data['username'],
            role=data['role'],  # Make sure this is a list, as it's expected to be JSONB
            organization=data['organization'],
            email=data['email']
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
    
    @staticmethod
    def get_all_users():
        return User.query.all()
    
    # @staticmethod
    # def get_users_by_organization(organization):
    #     return User.query.filter_by(organization=organization).all()
    @staticmethod
    def get_users_by_organization(organization):
        return User.query.filter(User.organization == organization, User.role != 'admin').all()

    from sqlalchemy import func

    @staticmethod
    def get_users_by_role(role):
        try:
            print(f"Fetching users with role: {role}")
            # Use JSONB @> operator to check if the role is contained in the array
            users = User.query.filter(User.role.op('@>')([role])).all()
            print(f"Fetched users: {users}")
            return users
        except Exception as e:
            print(f"Error fetching users by role: {e}")
            return []

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
 