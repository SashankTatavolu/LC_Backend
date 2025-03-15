from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token,jwt_required, get_jwt
from ..services.user_service import UserService
from datetime import timedelta
from ..services.measure_time import measure_response_time

user_blueprint = Blueprint('users', __name__)

@user_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('username') or not data.get('role') or not data.get('password') or not data.get('organization') or not data.get('email'):
        return jsonify({"error": "username, role, password, email, and organization are required and cannot be empty"}), 400

    # Ensure role is stored as a list
    if not isinstance(data['role'], list):
        data['role'] = [role.strip() for role in data['role'].split(',')]

    user = UserService.create_user(data)
    if user:
        return jsonify({"message": "User created successfully"}), 201
    return jsonify({"error": "Failed to create user"}), 400


@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = UserService.authenticate_user(data['username'], data['password'])
    if user:
        # Ensure 'role' is a proper list
        roles = user.role if isinstance(user.role, list) else [user.role]
        
        # Clean up roles if needed (e.g., remove curly braces)
        roles = [role.replace("{", "").replace("}", "") for role in roles]
        
        additional_claims = {
            "username": user.username,
            "role": roles,  # Use the cleaned-up role list
            "user_id": user.id
        }
        access_token = create_access_token(
            identity=user.username, 
            additional_claims=additional_claims, 
            expires_delta=timedelta(minutes=30)
        )
        return jsonify(access_token=access_token, role=roles), 200
    return jsonify({"error": "Invalid credentials"}), 401


@user_blueprint.route('/login/guest', methods=['POST'])
def login_guest():
    guest_claims = {"role": "guest"}
    access_token = create_access_token(identity="guest", additional_claims=guest_claims)
    return jsonify(access_token=access_token), 200

@user_blueprint.route('/all', methods=['GET'])
@jwt_required()
@measure_response_time
def get_all_users():
    users = UserService.get_all_users()
    users_data = []
    for user in users:
        # Ensure 'role' is a proper list
        roles = user.role if isinstance(user.role, list) else [user.role]
        
        # Clean up roles if needed (e.g., remove curly braces or unwanted characters)
        roles = [role.replace("{", "").replace("}", "") for role in roles]
        
        users_data.append({
            "id": user.id,
            "username": user.username,
            "role": roles,  # Return role as a JSON array
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "organization": user.organization,
            "email": user.email
        })
    return jsonify(users_data), 200


@user_blueprint.route('/by_organization/<organization>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_users_by_organization(organization):
    users = UserService.get_users_by_organization(organization)
    users_data = [{"id": user.id, "username": user.username, "role": user.role, "organization": user.organization, "created_at": user.created_at, "updated_at": user.updated_at} for user in users]
    return jsonify(users_data), 200

@user_blueprint.route('/by_role/<role>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_users_by_role(role):
    users = UserService.get_users_by_role(role)
    users_data = [{"id": user.id, "username": user.username, "role": user.role, "organization": user.organization, "created_at": user.created_at, "updated_at": user.updated_at} for user in users]
    return jsonify(users_data), 200



@user_blueprint.route('/details/<int:user_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_user_details(user_id):
    user = UserService.get_user_by_id(user_id)
    if user:
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization": user.organization
        }

        if user.role in ['annotator', 'reviewer']:
            user_data["projects_assigned"] = user.total_assigned_projects()
        elif user.role == 'admin':
            user_data["projects_uploaded"] = user.total_uploaded_projects()
        
        return jsonify(user_data), 200
    return jsonify({"error": "User not found"}), 404

