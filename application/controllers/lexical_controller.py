from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from application.services.lexical_service import LexicalService

lexical_blueprint = Blueprint('lexicals', __name__)

@lexical_blueprint.route('/segment/<int:segment_id>', methods=['GET'])
@jwt_required()
def get_lexicals_by_segment(segment_id):
    lexicals = LexicalService.get_lexicals_by_segment(segment_id)
    if lexicals:
        return jsonify([lexical.serialize() for lexical in lexicals]), 200
    return jsonify({"message": "No lexical conceptual data found for the given segment_id"}), 404


@lexical_blueprint.route('/segment/<int:segment_id>', methods=['POST', 'PUT'])
@jwt_required()
def manage_lexicals_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        lexicals = LexicalService.create_lexicals(segment_id, data)
        return jsonify([lexical.serialize() for lexical in lexicals]), 201

    elif request.method == 'PUT':
        success = LexicalService.update_lexicals_by_segment(segment_id, data.get('lexicals', []), is_finalized)
        return ('Update successful', 200) if success else ('No lexicals found', 404)


@lexical_blueprint.route('/segment/<int:segment_id>/is_concept_generated', methods=['GET'])
@jwt_required()
def check_is_concept_generated(segment_id):
    is_generated, column_count = LexicalService.is_concept_generated(segment_id)
    return jsonify({"is_concept_generated": is_generated, "column_count": column_count}), 200
