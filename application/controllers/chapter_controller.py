from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from flask_mail import Message
from application.services.chapter_service import ChapterService
from application.services.measure_time import measure_response_time
# from application.extensions import mail 

chapter_blueprint = Blueprint('chapters', __name__)


# @chapter_blueprint.route('/add', methods=['POST'])
# @jwt_required()
# def add_chapter():
#     jwt_claims = get_jwt()
#     data = request.get_json()
#     chapter = ChapterService.create_chapter(
#         project_id=data['project_id'],
#         name=data['name'],
#         uploaded_by_id=jwt_claims['user_id'],  # Assuming user_id is included in JWT claims
#         text=data['text']
#     )
#     return jsonify({'message': 'Chapter added successfully', 'chapter_id': chapter.id}), 201

@chapter_blueprint.route('/add', methods=['POST'])
@jwt_required()
@measure_response_time
def add_chapter():
    jwt_claims = get_jwt()
    data = request.get_json()

    # Create the chapter
    chapter = ChapterService.create_chapter(
        project_id=data['project_id'],
        name=data['name'],
        uploaded_by_id=jwt_claims['user_id'],
        text=data['text']
    )

    # Notify assigned users via email
    user_ids = data.get('user_ids', [])
    ChapterService.notify_users(user_ids, data['project_id'], chapter.name)

    return jsonify({'message': 'Chapter added successfully', 'chapter_id': chapter.id}), 201


# @chapter_blueprint.route('/by_project/<int:project_id>', methods=['GET'])
# @jwt_required()
# def get_chapters(project_id):
#     chapters = ChapterService.get_chapters_by_project(project_id)
#     chapters_data = [{'id': chapter.id, 'name': chapter.name, 'text': chapter.text, 'created_at': chapter.created_at,'uploaded_by': chapter.uploaded_by.username,'assigned_to': "N1","status": "completed" } for chapter in chapters]
#     return jsonify(chapters_data), 200

@chapter_blueprint.route('/by_project/<int:project_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_chapters(project_id):
    chapters = ChapterService.get_chapters_by_project(project_id)
    chapters_data = [
        {
            'id': chapter.id,
            'name': chapter.name,
            'text': chapter.text,
            'created_at': chapter.created_at,
            'uploaded_by': chapter.uploaded_by.username,
            'assigned_to': [user.username for user in chapter.assigned_users],
            'status': "completed"
        } for chapter in chapters
    ]
    return jsonify(chapters_data), 200

# @chapter_blueprint.route('/by_chapter/<int:chapter_id>', methods=['GET'])
# @jwt_required()
# def get_chapter(chapter_id):
#     chapters = ChapterService.get_chapters_by_chapter_id(chapter_id)
#     chapters_data = [{'id': chapter.id, 'name': chapter.name, 'text': chapter.text, 'created_at': chapter.created_at,'uploaded_by': chapter.uploaded_by.username,'assigned_to': "N1","status": "completed" } for chapter in chapters]
#     return jsonify(chapters_data), 200
@chapter_blueprint.route('/by_chapter/<int:chapter_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_chapter(chapter_id):
    chapter = ChapterService.get_chapters_by_chapter_id(chapter_id)
    print("chapter: ",chapter.id)
    if not chapter:
        return jsonify({'message': 'Chapter not found'}), 404

    chapter_data = {
        'id': chapter.id,
        'name': chapter.name,
        'text': chapter.text,
        'created_at': chapter.created_at,
        'uploaded_by': chapter.uploaded_by.username,
        'assigned_to': [user.username for user in chapter.assigned_users],
        'status': "completed"
    }
    return jsonify(chapter_data), 200

@chapter_blueprint.route('/by_chapter/<int:chapter_id>/text', methods=['GET'])
@jwt_required()
@measure_response_time
def get_chapter_text(chapter_id):
    chapter = ChapterService.get_chapters_by_chapter_id(chapter_id)
    if not chapter:
        return jsonify({'message': 'Chapter not found'}), 404

    return jsonify({'text': chapter.text}), 200


@chapter_blueprint.route('/by_chapter/<int:chapter_id>/assigned_users', methods=['GET'])
@jwt_required()
@measure_response_time
def get_assigned_users_to_chapter(chapter_id):
    assigned_users = ChapterService.get_users_assigned_to_chapter(chapter_id)
    if assigned_users is None:
        return jsonify({'message': 'Chapter not found'}), 404
    
    return jsonify(assigned_users), 200

# @chapter_blueprint.route('/by_chapter/<int:chapter_id>/segments', methods=['GET'])
# @jwt_required()
# def get_segments_by_chapter(chapter_id):
#     segments = ChapterService.get_segments_by_chapter_id(chapter_id)
#     if not segments:
#         return jsonify({'message': 'No segments found for the given chapter ID'}), 404

#     segments_data = [segment.serialize() for segment in segments]
#     return jsonify(segments_data), 200

@chapter_blueprint.route('/by_chapter/<int:chapter_id>/sentences_segments', methods=['GET'])
@jwt_required()
@measure_response_time
def get_sentences_and_segments(chapter_id):
    sentences = ChapterService.get_sentences_by_chapter_id(chapter_id)
    if not sentences:
        return jsonify({'message': 'No sentences found for the given chapter'}), 404

    sentence_ids = [sentence.id for sentence in sentences]
    segments = ChapterService.get_segments_by_sentence_ids(sentence_ids)
    # print(segments)

    sentences_data = []
    for sentence in sentences:
        sentence_segments = [segment.serialize(exclude_keys=['sentence_id']) for segment in segments if segment.sentence_id == sentence.id]
        sentences_data.append({
            'chapter_id': chapter_id,
            'id': sentence.id,
            'sentence_id': sentence.sentence_id,  
            'text': sentence.text,
            'segments': sentence_segments
            # 'segment_id': segments.segment_id
        })

    return jsonify(sentences_data), 200

@chapter_blueprint.route('/chapters/<int:chapter_id>/segments', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_indices(chapter_id):
    try:
        segment_indices = ChapterService.get_segment_indices_by_chapter(chapter_id)
        if segment_indices:
            return jsonify(segment_indices), 200
        else:
            return jsonify({"message": "No segments found for this chapter"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500