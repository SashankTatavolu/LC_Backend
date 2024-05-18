from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..services.user_service import UserService

user_blueprint = Blueprint('users', __name__)


@user_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user = UserService.create_user(data)
    if user:
        return jsonify({"message": "User created successfully"}), 201
    return jsonify({"error": "Failed to create user"}), 400


@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = UserService.authenticate_user(data['username'], data['password'])
    if user:
        additional_claims = {"username": user.username, "role": user.role, "user_id": user.id}
        access_token = create_access_token(identity=user.username, additional_claims=additional_claims)
        return jsonify(access_token=access_token), 200
    return jsonify({"error": "Invalid credentials"}), 401
