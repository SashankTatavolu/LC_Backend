# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required
# from application.services.sentence_service import SentenceService
# from application.services.measure_time import measure_response_time

# sentence_blueprint = Blueprint('sentences', __name__)

# @sentence_blueprint.route('/add', methods=['POST'])
# @jwt_required()
# @measure_response_time
# def add_multiple_sentences():
#     data = request.get_json()
#     chapter_id = data.get('chapter_id')
#     sentences = data.get('sentences') 

#     if not sentences or not chapter_id:
#         return jsonify({'error': 'Invalid data. Ensure chapter_id and sentences are provided.'}), 400

#     new_sentences = SentenceService.create_sentences(chapter_id, sentences)
#     return jsonify({'message': f'{len(new_sentences)} sentences added successfully, starting index from 1.'}), 201


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
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
    """
    Fetch all sentences and their IDs for a given chapter.
    """
    sentences = Sentence.query.filter_by(chapter_id=chapter_id).order_by(Sentence.sentence_index).all()

    if not sentences:
        return jsonify({'error': 'No sentences found for this chapter'}), 404

    return jsonify([
        {
            "id": sentence.id,
            "sentence_id": sentence.sentence_id,
            "sentence_index": sentence.sentence_index,
            "text": sentence.text
        } for sentence in sentences
    ]), 200
    