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
        return User.query.filter(
        User.organization == organization,
        ~User.role.op('?')('admin')  # Checks if 'admin' is NOT in the JSONB role
    ).all()

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
    
    
    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            print(f"User with ID {user_id} not found.")
            return None

        try:
            print(f"Updating user {user_id} with data: {data}")

            if 'username' in data and data['username']:
                print(f"Updating username from {user.username} to {data['username']}")
                user.username = data['username']

            if 'email' in data and data['email']:
                print(f"Updating email from {user.email} to {data['email']}")
                user.email = data['email']

            if 'organization' in data:
                print(f"Updating organization from {user.organization} to {data['organization']}")
                user.organization = data['organization']

            # Handle roles update
            if 'roles' in data:
                if isinstance(data['roles'], list):
                    print(f"Updating roles from {user.role} to {data['roles']}")
                    user.role = data['roles']
                else:
                    user.role = [role.strip() for role in data['roles'].split(',')]
                    print(f"Updated roles to {user.role}")

            if 'password' in data and data['password']:
                user.set_password(data['password'])
                print(f"Password updated for user {user_id}")

            db.session.flush()  # Pushes the changes to the DB immediately for verification
            db.session.commit()
            print(f"User {user_id} updated successfully with new data: {user.username}, {user.email}, {user.organization}, {user.role}")
            return user

        except Exception as e:
            print(f"Error updating user {user_id}: {e}")
            db.session.rollback()
            return None
