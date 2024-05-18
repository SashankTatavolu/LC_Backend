from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from application.services.project_service import ProjectService
from application.services.user_service import UserService
from application.models.user_model import User
from .decorators import admin_required

project_blueprint = Blueprint('projects', __name__)


@project_blueprint.route('/add', methods=['POST'])
@jwt_required()
@admin_required
def add_project():
    jwt_claims = get_jwt()

    data = request.get_json()
    project = ProjectService.create_project(
        name=data['name'],
        description=data.get('description', ''),
        language=data['language'],
        owner_id=jwt_claims['user_id']
    )
    return jsonify({'message': 'Project added successfully', 'project_id': project.id}), 201


@project_blueprint.route('/all', methods=['GET'])
@jwt_required()
def view_all_projects():
    projects = ProjectService.get_all_projects()
    projects_data = [{'id': project.id, 'name': project.name, 'language': project.language} for project in projects]
    return jsonify(projects_data), 200


@project_blueprint.route('/by_language/<language>', methods=['GET'])
@jwt_required()
def view_projects_by_language(language):
    projects = ProjectService.get_projects_by_language(language)
    projects_data = [{'id': project.id, 'name': project.name} for project in projects]
    return jsonify(projects_data), 200
