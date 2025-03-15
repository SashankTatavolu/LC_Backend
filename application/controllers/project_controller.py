from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from application.services.project_service import ProjectService
from application.services.user_service import UserService
from application.models.user_model import User
from application.models.chapter_model import Chapter
from .decorators import admin_required
from application.extensions import db
from application.models.sentence_model import Sentence
from application.models.segment_model import Segment
from application.services.measure_time import measure_response_time

project_blueprint = Blueprint('projects', __name__)


@project_blueprint.route('/add', methods=['POST'])
@jwt_required()
@measure_response_time
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
@measure_response_time
def view_all_projects():
    projects = ProjectService.get_all_projects()
    projects_data = []

    for project in projects:
        total_chapters = Chapter.query.filter_by(project_id=project.id).count()
        # Total segments in this project
        total_segments = db.session.query(Segment).join(Sentence).join(Chapter).filter(Chapter.project_id == project.id).count()
        print("total: ",total_segments)
        pending_segments = db.session.query(Segment).join(Sentence).join(Chapter).filter(
            Chapter.project_id == project.id,
            Segment.status == 'pending'  # Only pending segments
        ).count()
        print("pending: ",pending_segments)
        # total_segments = Segment.query.filter_by(project_id=project.id).count()
        # pending_segments = Segment.query.filter_by(project_id=project.id, status='pending').count()

        projects_data.append({
            'id': project.id,
            'name': project.name,
            'language': project.language,
            'created_at': project.created_at,
            'total_chapters': total_chapters,
            # 'total_segments': 50,
            'total_segments': 50,
            'pending_segments': 5
        })
    
    return jsonify(projects_data), 200



@project_blueprint.route('/by_language/<language>', methods=['GET'])
@jwt_required()
@measure_response_time
def view_projects_by_language(language):
    projects = ProjectService.get_projects_by_language(language)
    projects_data = [{'id': project.id, 'name': project.name} for project in projects]
    return jsonify(projects_data), 200

# @project_blueprint.route('/<int:project_id>/assign_user', methods=['POST'])
# @jwt_required()
# def assign_user_to_project(project_id):
#     data = request.get_json()
#     if not data.get('user_id') or not data.get('chapter_id'):
#         return jsonify({"error": "user_id and chapter_id are required"}), 400

#     success = ProjectService.assign_user_to_project(project_id, data['user_id'], data['chapter_id'])
#     if success:
#         return jsonify({"message": "User assigned to project and chapter successfully"}), 200
#     return jsonify({"error": "Failed to assign user to project and chapter"}), 400
@project_blueprint.route('/<int:project_id>/assign_users', methods=['POST'])
@jwt_required()
@measure_response_time
def assign_users_to_project_endpoint(project_id):
    data = request.get_json()
    user_ids = data.get('user_ids', [])
    chapter_id = data.get('chapter_id')

    if not user_ids or not chapter_id:
        return jsonify({"error": "user_ids and chapter_id are required"}), 400

    success = ProjectService.assign_users_to_project(project_id, user_ids, chapter_id)

    if success:
        return jsonify({"message": "Users assigned to project and chapter successfully"}), 200

    return jsonify({"error": "Failed to assign users to project and chapter"}), 400


@project_blueprint.route('/by_user/<int:user_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def view_projects_by_user(user_id):
    projects = ProjectService.get_projects_by_user(user_id)
    projects_data = [{'id': project.id, 'name': project.name, 'description': project.description, 'language': project.language, 'owner_id': project.owner_id} for project in projects]
    return jsonify(projects_data), 200


@project_blueprint.route('/by_organization/<organization>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_projects_by_user_organization(organization):
    projects = ProjectService.get_projects_by_user_organization(organization)
    projects_data = []

    for project in projects:
        total_chapters = Chapter.query.filter_by(project_id=project.id).count()
        projects_data.append({
            'id': project.id,
            'name': project.name,
            'language': project.language,
            'created_at': project.created_at,
            'total_chapters': total_chapters,
            'total_segments': 50,
            'pending_segments': 5
        })

    return jsonify(projects_data), 200