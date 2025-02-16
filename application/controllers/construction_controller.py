from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from application.services.construction_service import ConstructionService

construction_blueprint = Blueprint('construction', __name__)


@construction_blueprint.route('/segment/<int:segment_id>/construction', methods=['POST', 'PUT'])
@jwt_required()
def manage_construction_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        construction_entries = ConstructionService.create_construction_by_segment(segment_id, data)
        return jsonify([construction.serialize() for construction in construction_entries]), 201
    elif request.method == 'PUT':
        success = ConstructionService.update_construction_by_segment(segment_id, data.get('constructions', []), is_finalized)
        return ('Update successful', 200) if success else ('No construction data found', 404)
