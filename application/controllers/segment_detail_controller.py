from flask import Blueprint, Response, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from io import BytesIO
from application.extensions import db
from application.services.measure_time import measure_response_time

from application.services.segment_detail_service import SegmentDetailService

segment_detail_blueprint = Blueprint('segment_detail', __name__)

@segment_detail_blueprint.route('/process_text', methods=['POST'])
@jwt_required
@measure_response_time
def handle_process_text():
    data = request.get_json()
    if 'chapter_id' not in data or 'chapter_data' not in data:
        return jsonify({"error": "Both 'chapter_id' and 'chapter_data' fields are required in the JSON body"}), 400

    chapter_id = data['chapter_id']
    sentences = data['chapter_data']
    
    try:
        processed_results = SegmentDetailService.process_sentences(sentences, chapter_id)
        return jsonify({"chapter_id": chapter_id, "processed_results": processed_results}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@segment_detail_blueprint.route('/segment_details/<int:segment_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_details(segment_id):
    segment_details = SegmentDetailService.get_segment_details(segment_id)
    if segment_details:
        return jsonify(segment_details)
    else:
        return ('', 404)

@segment_detail_blueprint.route('/segment_details', methods=['POST'])
@jwt_required()
@measure_response_time
def create_segment_details():
    data = request.get_json()
    segment_id = SegmentDetailService.create_segment_details(data)
    if segment_id:
        return jsonify({'message': 'Segment details created/updated successfully', 'segment_id': segment_id}), 201
    else:
        return jsonify({'message': 'Failed to create/update segment details'}), 400
    

@segment_detail_blueprint.route('/segment_details/<int:segment_id>/download', methods=['GET'])
@jwt_required()
@measure_response_time
def download_segment_details(segment_id):
    segment_details = SegmentDetailService.get_segment_details_as_text(segment_id)
    if not segment_details:
        return ('', 404)

    # Convert the text data to bytes and create a BytesIO object
    file_obj = BytesIO(segment_details.encode('utf-8'))

    # Send the file to the user
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=f"segment_{segment_id}.txt",
        mimetype="text/plain"
    )

@segment_detail_blueprint.route('/segment_details/<int:segment_id>/csv', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_details_csv(segment_id):
    segment_details = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
    if segment_details:
        # Return as plain text with content type 'text/plain'
        return segment_details, 200, {'Content-Type': 'text/plain'}
    else:
        return 'Data not found', 404


@segment_detail_blueprint.route('/segment_details/<int:segment_id>/previous_csv', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_details_csv_multiple(segment_id):
    segment_details = SegmentDetailService.get_segment_details_as_csv(segment_id)
    if segment_details:
        # Return as plain text with content type 'text/plain'
        return segment_details, 200, {'Content-Type': 'text/plain'}
    else:
        return 'Data not found', 404


@segment_detail_blueprint.route('/segment_details/<int:segment_id>/download_xml', methods=['GET'])
@jwt_required()
@measure_response_time
def download_segment_details_xml(segment_id):
    # Fetch the segment details using the service function
    segment_details = SegmentDetailService.get_segment_details_as_dict(segment_id)
    
    # If no segment details are found, return 404
    if not segment_details:
        return ('', 404)

    # Generate the XML content
    xml_content = SegmentDetailService.generate_segment_details_xml(segment_details)

    # Return the XML as a downloadable file
    response = Response(xml_content, mimetype='application/xml')
    response.headers['Content-Disposition'] = f'attachment; filename=segment_{segment_id}.xml'

    return response

@segment_detail_blueprint.route('/chapter_segments/<int:chapter_id>/download', methods=['GET'])
@jwt_required()
@measure_response_time
def download_all_segments_for_chapter(chapter_id):
    chapter_segments = SegmentDetailService.get_all_segments_for_chapter_as_text(chapter_id)
    if not chapter_segments:
        return ('', 404)

    # Convert the text data to bytes and create a BytesIO object
    file_obj = BytesIO(chapter_segments.encode('utf-8'))

    # Send the file to the user
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=f"chapter_{chapter_id}_segments.txt",
        mimetype="text/plain"
    )


@segment_detail_blueprint.route('/segment_details/<int:segment_id>/previous', methods=['GET'])
@jwt_required()
@measure_response_time
def get_previous_segment_details(segment_id):
    # Call the service method to fetch the previous segment's details
    previous_segment_details = SegmentDetailService.get_previous_segment_details(segment_id)
    
    if previous_segment_details:
        return jsonify(previous_segment_details)
    else:
        return ('', 404)
