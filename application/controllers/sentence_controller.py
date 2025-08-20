from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.extensions import db
from application.models.segment_model import Segment
from application.services.sentence_service import SentenceService
from application.models.sentence_model import Sentence
from application.services.measure_time import measure_response_time

sentence_blueprint = Blueprint('sentences', __name__)

@sentence_blueprint.route('/add', methods=['POST'])
@jwt_required()
@measure_response_time
def add_multiple_sentences():
    if 'file' not in request.files or 'chapter_id' not in request.form:
        return jsonify({'error': 'Missing file or chapter_id'}), 400

    file = request.files['file']
    chapter_id = request.form['chapter_id']

    if not file or not chapter_id:
        return jsonify({'error': 'Invalid data. Ensure chapter_id and file are provided.'}), 400

    # Read file content
    file_content = [line.strip() for line in file.read().decode('utf-8').splitlines() if line.strip()]
    print(f"Read {len(file_content)} lines from file")  # Debugging output

    new_sentences = SentenceService.create_sentences(chapter_id, file_content)
    return jsonify({'message': f'{len(new_sentences)} sentences added successfully'}), 201

    
@sentence_blueprint.route('/chapter/<int:chapter_id>/sentences', methods=['GET'])
@jwt_required()
@measure_response_time
def get_sentences_by_chapter(chapter_id):
    # Subquery to get the first segment per sentence
    subquery = (
        db.session.query(Segment)
        .filter(Segment.chapter_id == chapter_id)
        .distinct(Segment.sentence_id)
        .subquery()
    )

    # Join Sentence with the subquery
    results = (
        db.session.query(
            Sentence.id,
            Sentence.sentence_id,
            Sentence.sentence_index,
            Sentence.text,
            subquery.c.english_text,
            subquery.c.wx_text
        )
        .outerjoin(subquery, subquery.c.sentence_id == Sentence.id)
        .filter(Sentence.chapter_id == chapter_id)
        .order_by(Sentence.sentence_index)
        .all()
    )

    # Serialize results
    response = []
    for row in results:
        response.append({
            "id": row.id,
            "sentence_id": row.sentence_id,
            "sentence_index": row.sentence_index,
            "text": row.text,
            "english_text": row.english_text,
            "wx_text": row.wx_text,
        })

    return jsonify(response), 200