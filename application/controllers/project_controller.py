from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from application.services.project_service import ProjectService
from application.services.user_service import UserService
from application.models.user_model import User
from application.models.chapter_model import Chapter
from .decorators import admin_required
from application.extensions import db
from application.models.sentence_model import Sentence
from application.models.segment_model import Segment
from application.services.measure_time import measure_response_time
from application.services.chapter_service import ChapterService
from application.services.segment_service import SegmentService
from application.models.project_model import Project

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
    jwt_data = get_jwt()
    user_id = jwt_data.get('user_id')

    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"message": "User not found"}), 404

    # Now filter projects by the user's organization
    projects = Project.query.join(User, Project.owner_id == User.id)\
        .filter(User.organization == current_user.organization).all()

    projects_data = []
    for project in projects:
        total_chapters = Chapter.query.filter_by(project_id=project.id).count()
        total_segments = db.session.query(Segment).join(Sentence).join(Chapter).filter(Chapter.project_id == project.id).count()
        pending_segments = db.session.query(Segment).join(Sentence).join(Chapter).filter(
            Chapter.project_id == project.id,
            Segment.status == 'pending'
        ).count()

        projects_data.append({
            'id': project.id,
            'name': project.name,
            'language': project.language,
            'created_at': project.created_at,
            'total_chapters': total_chapters,
            'total_segments': total_segments,
            'pending_segments': pending_segments
        })

    return jsonify(projects_data), 200

@project_blueprint.route('/by_language/<language>', methods=['GET'])
@jwt_required()
@measure_response_time
def view_projects_by_language(language):
    projects = ProjectService.get_projects_by_language(language)
    projects_data = [{'id': project.id, 'name': project.name} for project in projects]
    return jsonify(projects_data), 200



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


@project_blueprint.route('/<int:project_id>/overview', methods=['GET'])
@jwt_required()
def get_project_overview(project_id):
    """
    Get project overview with chapter count, total segments, completed segments, pending segments,
    and a list of chapter IDs.
    """
    try:
        # Get all chapters for the project
        chapters = ChapterService.get_chapters_by_project(project_id)
        total_chapters = len(chapters)
        
        total_segments = 0
        completed_segments = 0
        chapter_ids = []

        for chapter in chapters:
            chapter_ids.append(chapter.id)
            chapter_segments = SegmentService.get_segments_count_by_chapter(chapter.id)
            completed_chapter_segments = SegmentService.get_completed_segments_count_by_chapter(chapter.id)

            total_segments += chapter_segments
            completed_segments += completed_chapter_segments

        pending_segments = total_segments - completed_segments

        return jsonify({
            'project_id': project_id,
            'total_chapters': total_chapters,
            'chapter_ids': chapter_ids,
            'total_segments': total_segments,
            'completed_segments': completed_segments,
            'pending_segments': pending_segments
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
