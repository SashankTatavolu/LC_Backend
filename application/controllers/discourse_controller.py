from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.discourse_service import DiscourseService

discourse_blueprint = Blueprint('discourse', __name__)

@discourse_blueprint.route('/segment/<int:segment_id>/discourse', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_discourse_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        discourse_entries = DiscourseService.create_discourse_by_segment(segment_id, data)
        return jsonify([discourse.serialize() for discourse in discourse_entries]), 201
    elif request.method == 'PUT':
        success = DiscourseService.update_discourse_by_segment(segment_id, data.get('discourse', []), is_finalized)
        return ('Update successful', 200) if success else ('No discourse data found', 404)

