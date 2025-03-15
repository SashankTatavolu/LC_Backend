from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time

from application.services.segment_service import SegmentService

segment_blueprint = Blueprint('segments', __name__)

@segment_blueprint.route('/convert_to_wx/format', methods=['POST'])
@jwt_required()
@measure_response_time
def get_wx_format():
    data = request.json
    
    # Ensure 'text' is provided in the request and is a list
    if 'text' not in data or not isinstance(data['text'], list):
        return jsonify({'error': "'text' must be a list of sentences"}), 400
    
    input_texts = data['text']
    results = []
    
    for input_text in input_texts:
        # Convert each text to WX format
        wx_output = SegmentService.text_to_wx(input_text)
        results.append(wx_output)
    
    # Return the results as a list
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
    data = request.get_json()
    segment = SegmentService.create_segment(data)
    return jsonify(segment.serialize()), 201

@segment_blueprint.route('/sentence/<int:sentence_id>', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def segments_by_sentence(sentence_id):
    data = request.get_json()
    if request.method == 'POST':
        segments = SegmentService.create_segments(sentence_id, data)
        return jsonify([s.serialize() for s in segments]), 201
    elif request.method == 'PUT':
        segments = SegmentService.update_segments_by_sentence(sentence_id, data)
        return jsonify([s.serialize() for s in segments]) if segments else ('No segments found', 404)

@segment_blueprint.route('/<int:chapter_id>/segment_count', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segments_count(chapter_id):
    """
    API to get the number of segments in a specific chapter.
    
    :param chapter_id: ID of the chapter.
    :return: JSON response with the segment count.
    """
    try:
        # Get the segment count using the service
        segment_count = SegmentService.get_segments_count_by_chapter(chapter_id)
        return jsonify({'chapter_id': chapter_id, 'segment_count': segment_count}), 200
    except Exception as e:
        # Handle exceptions and return an error response
        return jsonify({'error': str(e)}), 500
    
    
@segment_blueprint.route('/segment/finalized-status/<int:segment_id>', methods=['GET'])
def fetch_is_finalized(segment_id):
    """
    API to fetch isFinalized status of all tables for a given segment_id.
    """
    try:
        status = SegmentService.get_is_finalized_status(segment_id)
        return jsonify({"success": True, "data": status}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
