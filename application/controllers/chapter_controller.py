from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from application.services.chapter_service import ChapterService

chapter_blueprint = Blueprint('chapters', __name__)


@chapter_blueprint.route('/add', methods=['POST'])
@jwt_required()
def add_chapter():
    jwt_claims = get_jwt()
    data = request.get_json()
    chapter = ChapterService.create_chapter(
        project_id=data['project_id'],
        name=data['name'],
        uploaded_by_id=jwt_claims['user_id'],  # Assuming user_id is included in JWT claims
        text=data['text']
    )
    return jsonify({'message': 'Chapter added successfully', 'chapter_id': chapter.id}), 201


@chapter_blueprint.route('/by_project/<int:project_id>', methods=['GET'])
@jwt_required()
def get_chapters(project_id):
    chapters = ChapterService.get_chapters_by_project(project_id)
    chapters_data = [{'id': chapter.id, 'name': chapter.name, 'text': chapter.text} for chapter in chapters]
    return jsonify(chapters_data), 200
