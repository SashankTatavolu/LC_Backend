from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.sentence_service import SentenceService

sentence_blueprint = Blueprint('sentences', __name__)

@sentence_blueprint.route('/add', methods=['POST'])
@jwt_required()
def add_multiple_sentences():
    data = request.get_json()
    chapter_id = data.get('chapter_id')
    sentences = data.get('sentences') 

    if not sentences or not chapter_id:
        return jsonify({'error': 'Invalid data. Ensure chapter_id and sentences are provided.'}), 400

    new_sentences = SentenceService.create_sentences(chapter_id, sentences)
    return jsonify({'message': f'{len(new_sentences)} sentences added successfully, starting index from 1.'}), 201
