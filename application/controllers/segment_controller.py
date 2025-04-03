import csv
import io
from application.extensions import db
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.models.sentence_model import Sentence
from application.models.assignment_model import Assignment
from application.services.measure_time import measure_response_time
from application.services.segment_service import SegmentService
from application.models.segment_model import Segment

segment_blueprint = Blueprint('segments', __name__)

@segment_blueprint.route('/convert_to_wx/format', methods=['POST'])
@jwt_required()
@measure_response_time
def get_wx_format():
    data = request.json
    
    if 'text' not in data or not isinstance(data['text'], list):
        return jsonify({'error': "'text' must be a list of sentences"}), 400
    
    input_texts = data['text']
    results = [SegmentService.text_to_wx(text) for text in input_texts]

    return jsonify({'wx_formats': results})


@segment_blueprint.route('/<int:segment_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@measure_response_time
def segment(segment_id):
    if request.method == 'GET':
        segment = SegmentService.get_segment_by_id(segment_id)
        return jsonify(segment.serialize()) if segment else ('', 404)

    elif request.method == 'PUT':
        data = request.get_json()
        segment = SegmentService.update_segment(segment_id, data)
        return jsonify(segment.serialize()) if segment else ('', 404)

    elif request.method == 'DELETE':
        result = SegmentService.delete_segment(segment_id)
        return ('segment deleted', 204) if result else ('', 404)


@segment_blueprint.route('/', methods=['POST'])
@jwt_required()
@measure_response_time
def create_segment():
    """
    Create a new segment with required fields.
    """
    data = request.get_json()
    
    # Ensure required fields are present
    required_fields = ['sentence_id', 'segment_index', 'segment_text', 'chapter_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
    
    segment = SegmentService.create_segment(data)
    return jsonify(segment.serialize()), 201


@segment_blueprint.route('/sentence/<int:sentence_id>', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def segments_by_sentence(sentence_id):
    """
    Create or update multiple segments for a sentence.
    """
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({'error': 'Data should be a list of segment objects'}), 400

    # Extract chapter_id from the first segment (assuming all segments have the same chapter_id)
    chapter_id = data[0].get('chapter_id')

    if request.method == 'POST':
        segments = SegmentService.create_segments(sentence_id, chapter_id, data)
        return jsonify([s.serialize() for s in segments]), 201

    elif request.method == 'PUT':
        updated_segments = []
        for segment_data in data:
            segment_id = segment_data.get('segment_id')
            if segment_id:
                updated_segment = SegmentService.update_segment(segment_id, segment_data)
                if updated_segment:
                    updated_segments.append(updated_segment.serialize())

        return jsonify(updated_segments) if updated_segments else ('No segments found', 404)


@segment_blueprint.route('/segments', methods=['PUT'])
@jwt_required()
@measure_response_time
def update_segments():
    """
    Update multiple segments using segment_id.
    """
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({'error': 'Data should be a list of segment objects'}), 400

    updated_segments = []
    for segment_data in data:
        segment_id = segment_data.get('segment_id')
        if segment_id:
            updated_segment = SegmentService.update_segment(segment_id, segment_data)
            if updated_segment:
                updated_segments.append(updated_segment.serialize())

    return jsonify(updated_segments) if updated_segments else ('No segments found', 404)


@segment_blueprint.route('/<int:chapter_id>/segment_count', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segments_count(chapter_id):
    """
    Get the total number of segments in a chapter and the number of fully completed ones.
    """
    try:
        total_segments = SegmentService.get_segments_count_by_chapter(chapter_id)
        completed_segments = SegmentService.get_completed_segments_count_by_chapter(chapter_id)

        return jsonify({
            'chapter_id': chapter_id,
            'total_segments': total_segments,
            'completed_segments': completed_segments
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segment_blueprint.route('/upload_segments', methods=['POST'])
@jwt_required()
@measure_response_time
def upload_segments():
    """
    Upload multiple segments from a text file.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Missing file'}), 400

    file = request.files['file']
    file_format = file.filename.split('.')[-1].lower()

    if file_format != 'txt':
        return jsonify({'error': 'Unsupported file format. Only TXT is allowed.'}), 400

    segments_data = []

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        lines = stream.readlines()

        for line in lines:
            parts = line.strip().split("\t")  # Split by tab

            # Ensure there are at least 2 parts (segment_index & segment_text)
            if len(parts) < 2:
                print(f"Skipping invalid line: {line}")
                continue

            segment_index = parts[0]
            segment_text = parts[1]
            wx_text = parts[2] if len(parts) > 2 else None  # Handle missing WX text
            english_text = parts[3] if len(parts) > 3 else None  # Handle missing English text

            # Extract sentence_id from segment_index
            extracted_sentence_id = re.sub(r'[a-zA-Z]+$', '', segment_index)

            # Find corresponding sentence_id
            sentence = db.session.query(Sentence).filter(
                Sentence.sentence_id == extracted_sentence_id
            ).first()

            if not sentence:
                print(f"Sentence with id {extracted_sentence_id} not found.")
                continue  # Skip if sentence is not found

            segments_data.append({
                'sentence_id': sentence.id,  # Use actual sentence ID
                'segment_index': segment_index,
                'segment_text': segment_text,
                'wx_text': wx_text,
                'english_text': english_text,
                'chapter_id': sentence.chapter_id,  # Get chapter_id from sentence
                'segment_type': " ",  # Placeholder
                'index_type': "type",  # Placeholder
            })

        # Save to database
        created_segments = SegmentService.create_segments_bulk(segments_data)
        return jsonify({'message': f'{len(created_segments)} segments uploaded successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segment_blueprint.route('/assign_user', methods=['POST'])
@jwt_required()
def assign_user_to_segment():
    """
    API to assign a user to a specific tab of a segment.
    """
    data = request.get_json()
    
    user_id = data.get('user_id')
    segment_id = data.get('segment_id')
    tab_name = data.get('tab_name')  # e.g., 'lexical_conceptual'

    if not all([user_id, segment_id, tab_name]):
        return jsonify({'error': 'user_id, segment_id, and tab_name are required'}), 400

    result = SegmentService.assign_user_to_tab(user_id, segment_id, tab_name)
    
    if isinstance(result, Assignment):
        return jsonify(result.serialize()), 201  # Ensure serialization
    else:
        return jsonify(result), 400



@segment_blueprint.route('/assigned_users/<int:segment_id>/<string:tab_name>', methods=['GET'])
@jwt_required()
def get_assigned_users(segment_id, tab_name):
    """
    API to fetch users assigned to a specific tab of a segment.
    """
    users = SegmentService.get_assigned_users(segment_id, tab_name)
    return jsonify(users), 200


@segment_blueprint.route('/segments/<int:chapter_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segments_by_chapter(chapter_id):
    """
    Fetch segment IDs along with segment indexes for a given chapter ID.
    """
    try:
        segments = Segment.query.filter_by(chapter_id=chapter_id).all()
        result = [{'segment_id': segment.segment_id, 'segment_index': segment.segment_index} for segment in segments]
        return jsonify({'chapter_id': chapter_id, 'segments': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segment_blueprint.route('/segment/finalized-status/<int:segment_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def fetch_is_finalized(segment_id):
    """
    Fetch `isFinalized` status for all related tables based on segment_id.
    """
    try:
        status = SegmentService.get_is_finalized_status(segment_id)
        return jsonify({"success": True, "data": status}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@segment_blueprint.route('/<int:chapter_id>/finalized_counts', methods=['GET'])
@jwt_required()
@measure_response_time
def get_finalized_counts(chapter_id):
    """
    Get the count of finalized lexical, relational, construction, and discourse segments for a chapter.
    """
    try:
        counts = SegmentService.get_finalized_counts_by_chapter(chapter_id)
        return jsonify({
            'chapter_id': chapter_id,
            'total_segments': counts["total_segments"],
            'lexical_finalized': counts["lexical_finalized"],
            'relational_finalized': counts["relational_finalized"],
            'construction_finalized': counts["construction_finalized"],
            'discourse_finalized': counts["discourse_finalized"]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
