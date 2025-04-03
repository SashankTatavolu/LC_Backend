from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.relational_service import RelationalService

relational_blueprint = Blueprint('relational', __name__)

@relational_blueprint.route('/segment/<int:segment_id>/relational', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_relational_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        relational_entries = RelationalService.create_relational_by_segment(segment_id, data)
        return jsonify([relational.serialize() for relational in relational_entries]), 201
    elif request.method == 'PUT':
        success = RelationalService.update_relational_by_segment(segment_id, data.get('relational', []), is_finalized)
        return ('Update successful', 200) if success else ('Failed to update relational data', 400)
