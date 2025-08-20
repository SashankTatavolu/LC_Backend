from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.lexical_service import LexicalService

lexical_blueprint = Blueprint('lexicals', __name__)

@lexical_blueprint.route('/segment/<int:segment_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_lexicals_by_segment(segment_id):
    lexicals = LexicalService.get_lexicals_by_segment(segment_id)
    if lexicals:
        return jsonify([lexical.serialize() for lexical in lexicals]), 200
    return jsonify({"message": "No lexical conceptual data found for the given segment_id"}), 404


@lexical_blueprint.route('/segment/<int:segment_id>', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_lexicals_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)

    print(f"Received PUT /segment/{segment_id} payload: {data}")

    if request.method == 'POST':
        lexicals = LexicalService.create_lexicals(segment_id, data)
        return jsonify([lexical.serialize() for lexical in lexicals]), 201

    elif request.method == 'PUT':
        success, message = LexicalService.update_lexicals_by_segment(
            segment_id,
            data.get('lexicals', []),
            is_finalized
        )
        if success:
            return jsonify({"message": "Update successful"}), 200
        else:
            return jsonify({"message": "Update failed", "error": message}), 400


@lexical_blueprint.route('/segment/<int:segment_id>/is_concept_generated', methods=['GET'])
@jwt_required()
@measure_response_time
def check_is_concept_generated(segment_id):
    is_generated, column_count = LexicalService.is_concept_generated(segment_id)
    return jsonify({"is_concept_generated": is_generated, "column_count": column_count}), 200

